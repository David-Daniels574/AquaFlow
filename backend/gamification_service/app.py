import logging
import os
import time
import uuid
from datetime import datetime

import psycopg2
import requests
from flask import Flask, g, has_request_context, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity, jwt_required
from prometheus_flask_exporter import PrometheusMetrics
from requests.adapters import HTTPAdapter
from sqlalchemy import distinct, func
from sqlalchemy.exc import OperationalError
from urllib3.util.retry import Retry

try:
    from .models import (
        Broadcast,
        Challenge,
        ConservationTip,
        DiscussionThread,
        ThreadComment,
        UserChallenge,
        db,
    )
except ImportError:
    from models import Broadcast, Challenge, ConservationTip, DiscussionThread, ThreadComment, UserChallenge, db


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = "-"
        if has_request_context():
            record.correlation_id = getattr(g, "correlation_id", "-")
        return True


def configure_logging():
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [corr_id=%(correlation_id)s] %(name)s - %(message)s"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)


def create_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.25,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    return session


def create_app():
    configure_logging()
    app = Flask(__name__)

    database_uri = os.environ.get("GAMIFICATION_DATABASE_URL") or os.environ.get("DATABASE_URL", "sqlite:///gamification.db")
    if database_uri.startswith("postgres://"):
        database_uri = database_uri.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["INTERNAL_SERVICE_TOKEN"] = os.environ.get("INTERNAL_SERVICE_TOKEN", "internal-dev-token")
    app.config["AUTH_SERVICE_URL"] = os.environ.get("AUTH_SERVICE_URL", "http://auth_service:5000")
    app.config["SERVICE_TIMEOUT_SECONDS"] = float(os.environ.get("SERVICE_TIMEOUT_SECONDS", "5"))

    db.init_app(app)
    CORS(app)
    JWTManager(app)
    PrometheusMetrics(app)

    http_session = create_session()

    @app.before_request
    def attach_correlation_id():
        g.correlation_id = request.headers.get("X-Correlation-ID") or f"req-{uuid.uuid4().hex[:12]}"

    @app.after_request
    def add_correlation_header(response):
        response.headers["X-Correlation-ID"] = g.correlation_id
        return response

    def require_internal_auth():
        return request.headers.get("X-Internal-Service-Token") == app.config["INTERNAL_SERVICE_TOKEN"]

    def call_internal_service(base_url, method, path, *, payload=None, expected_status=(200,)):
        url = f"{base_url.rstrip('/')}{path}"
        headers = {
            "X-Correlation-ID": g.correlation_id,
            "X-Internal-Service-Token": app.config["INTERNAL_SERVICE_TOKEN"],
        }
        try:
            response = http_session.request(
                method=method,
                url=url,
                json=payload,
                headers=headers,
                timeout=app.config["SERVICE_TIMEOUT_SECONDS"],
            )
        except requests.RequestException as exc:
            app.logger.error("Inter-service call failed: %s %s (%s)", method, url, exc)
            return None, 502

        if response.status_code not in expected_status:
            app.logger.error(
                "Inter-service call returned %s for %s %s: %s",
                response.status_code,
                method,
                url,
                response.text[:300],
            )
            return None, response.status_code

        if not response.content:
            return {}, response.status_code
        return response.json(), response.status_code

    def get_user_context(user_id):
        payload, status = call_internal_service(
            app.config["AUTH_SERVICE_URL"], "GET", f"/internal/users/{user_id}", expected_status=(200, 404)
        )
        if status == 200:
            return payload
        return None

    def get_user_batch(user_ids):
        payload, status = call_internal_service(
            app.config["AUTH_SERVICE_URL"],
            "POST",
            "/internal/users/batch",
            payload={"user_ids": user_ids},
            expected_status=(200,),
        )
        if status != 200:
            return {}
        return {user["id"]: user for user in payload.get("users", [])}

    def wait_for_db():
        if "postgresql" not in app.config["SQLALCHEMY_DATABASE_URI"]:
            return
        retries = 8
        while retries > 0:
            try:
                conn = psycopg2.connect(app.config["SQLALCHEMY_DATABASE_URI"])
                conn.close()
                return
            except psycopg2.OperationalError:
                time.sleep(2)
                retries -= 1
        app.logger.warning("Database readiness check timed out for gamification_service")

    with app.app_context():
        wait_for_db()
        try:
            db.create_all()
        except OperationalError:
            app.logger.warning("Gamification service tables already created by another worker")

    @app.route("/", methods=["GET"])
    def health():
        return jsonify({"service": "gamification_service", "status": "ok"}), 200

    @app.route("/ping", methods=["GET"])
    def ping():
        return jsonify({"message": "pong", "service": "gamification_service"}), 200

    @app.route("/conservation_tips", methods=["GET"])
    def conservation_tips():
        location = request.args.get("location", "urban_india")
        tips = ConservationTip.query.filter_by(location_specific=location).all()
        return jsonify([{"title": tip.title, "content": tip.content} for tip in tips]), 200

    @app.route("/challenges", methods=["GET"])
    @jwt_required()
    def challenges():
        challenge_rows = Challenge.query.all()
        return jsonify(
            [
                {
                    "id": challenge.id,
                    "name": challenge.name,
                    "short_desc": challenge.short_desc,
                    "full_desc": challenge.full_desc,
                    "water_save_potential": challenge.water_save_potential,
                    "eco_points": challenge.eco_points,
                }
                for challenge in challenge_rows
            ]
        ), 200

    @app.route("/start_challenge/<int:challenge_id>", methods=["POST"])
    @jwt_required()
    def start_challenge(challenge_id):
        user_id = int(get_jwt_identity())
        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"error": "Challenge not found"}), 404
        existing = UserChallenge.query.filter_by(user_id=user_id, challenge_id=challenge_id).first()
        if existing:
            return jsonify({"error": "Challenge already started"}), 400

        user_challenge = UserChallenge(
            user_id=user_id,
            challenge_id=challenge_id,
            status="active",
            start_date=datetime.utcnow(),
        )
        db.session.add(user_challenge)
        db.session.commit()
        return jsonify({"message": "Challenge started", "user_challenge_id": user_challenge.id}), 201

    @app.route("/user_challenges", methods=["GET"])
    @jwt_required()
    def user_challenges():
        user_id = int(get_jwt_identity())
        rows = UserChallenge.query.filter_by(user_id=user_id).all()
        payload = []
        for row in rows:
            challenge = Challenge.query.get(row.challenge_id)
            payload.append(
                {
                    "id": row.id,
                    "challenge_id": row.challenge_id,
                    "name": challenge.name if challenge else None,
                    "short_desc": challenge.short_desc if challenge else None,
                    "full_desc": challenge.full_desc if challenge else None,
                    "progress": row.progress,
                    "status": row.status,
                    "start_date": row.start_date.isoformat() if row.start_date else None,
                    "end_date": row.end_date.isoformat() if row.end_date else None,
                    "water_saved": row.water_saved,
                    "eco_points_earned": row.eco_points_earned,
                }
            )
        return jsonify(payload), 200

    @app.route("/update_challenge_progress/<int:user_challenge_id>", methods=["PUT"])
    @jwt_required()
    def update_challenge_progress(user_challenge_id):
        user_id = int(get_jwt_identity())
        progress = (request.json or {}).get("progress")
        if progress is None:
            return jsonify({"error": "Missing progress"}), 400
        try:
            progress = float(progress)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid progress value"}), 400

        user_challenge = db.session.get(UserChallenge, user_challenge_id)
        if not user_challenge or user_challenge.user_id != user_id:
            return jsonify({"error": "Unauthorized or not found"}), 403

        user_challenge.progress = progress
        if user_challenge.progress >= 100:
            challenge = db.session.get(Challenge, user_challenge.challenge_id)
            user_challenge.status = "completed"
            user_challenge.end_date = datetime.utcnow()
            user_challenge.water_saved = challenge.water_save_potential if challenge else 0
            user_challenge.eco_points_earned = challenge.eco_points if challenge else 0
        db.session.commit()
        return jsonify({"message": "Progress updated"}), 200

    @app.route("/community/broadcasts", methods=["GET", "POST"])
    @jwt_required()
    def handle_broadcasts():
        user = get_user_context(int(get_jwt_identity()))
        if not user or not user.get("society_id"):
            return jsonify({"error": "User not in a society"}), 403

        if request.method == "GET":
            broadcasts = Broadcast.query.filter_by(society_id=user["society_id"]).order_by(Broadcast.created_at.desc()).all()
            return jsonify(
                [
                    {
                        "id": broadcast.id,
                        "title": broadcast.title,
                        "content": broadcast.content,
                        "created_at": broadcast.created_at.isoformat(),
                    }
                    for broadcast in broadcasts
                ]
            ), 200

        claims = get_jwt()
        if claims.get("role") != "society_admin":
            return jsonify({"error": "Only admins can post broadcasts"}), 403

        data = request.json or {}
        if not data.get("title") or not data.get("content"):
            return jsonify({"error": "Missing title or content"}), 400
        broadcast = Broadcast(society_id=user["society_id"], title=data["title"], content=data["content"])
        db.session.add(broadcast)
        db.session.commit()
        return jsonify({"message": "Broadcast posted successfully"}), 201

    @app.route("/community/threads", methods=["GET", "POST"])
    @jwt_required()
    def handle_threads():
        user_id = int(get_jwt_identity())
        user = get_user_context(user_id)
        if not user or not user.get("society_id"):
            return jsonify({"error": "User not in a society"}), 403

        if request.method == "GET":
            threads = DiscussionThread.query.filter_by(society_id=user["society_id"]).order_by(DiscussionThread.created_at.desc()).all()
            author_lookup = get_user_batch([thread.user_id for thread in threads])
            return jsonify(
                [
                    {
                        "id": thread.id,
                        "title": thread.title,
                        "content": thread.content,
                        "category": thread.category,
                        "author": author_lookup.get(thread.user_id, {}).get("username", "Unknown"),
                        "created_at": thread.created_at.isoformat(),
                        "comment_count": thread.comments.count(),
                    }
                    for thread in threads
                ]
            ), 200

        data = request.json or {}
        if not data.get("title") or not data.get("content"):
            return jsonify({"error": "Missing title or content"}), 400
        thread = DiscussionThread(
            society_id=user["society_id"],
            user_id=user_id,
            title=data["title"],
            content=data["content"],
            category=data.get("category", "General"),
        )
        db.session.add(thread)
        db.session.commit()
        return jsonify({"message": "Thread created", "id": thread.id}), 201

    @app.route("/community/threads/<int:thread_id>/comments", methods=["GET", "POST"])
    @jwt_required()
    def handle_comments(thread_id):
        thread = DiscussionThread.query.get(thread_id)
        if not thread:
            return jsonify({"error": "Thread not found"}), 404

        if request.method == "GET":
            comments = ThreadComment.query.filter_by(thread_id=thread_id).order_by(ThreadComment.created_at.asc()).all()
            author_lookup = get_user_batch([comment.user_id for comment in comments])
            return jsonify(
                [
                    {
                        "id": comment.id,
                        "content": comment.content,
                        "author": author_lookup.get(comment.user_id, {}).get("username", "Unknown"),
                        "created_at": comment.created_at.isoformat(),
                    }
                    for comment in comments
                ]
            ), 200

        data = request.json or {}
        if not data.get("content"):
            return jsonify({"error": "Missing content"}), 400
        comment = ThreadComment(thread_id=thread_id, user_id=int(get_jwt_identity()), content=data["content"])
        db.session.add(comment)
        db.session.commit()
        return jsonify({"message": "Comment added"}), 201

    @app.route("/internal/users/<int:user_id>/summary", methods=["GET"])
    def internal_user_summary(user_id):
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403
        now = datetime.utcnow()
        this_month_start = datetime(now.year, now.month, 1)
        water_saved_month = (
            db.session.query(func.sum(UserChallenge.water_saved))
            .filter(UserChallenge.user_id == user_id, UserChallenge.end_date >= this_month_start)
            .scalar()
            or 0.0
        )
        active_count = UserChallenge.query.filter_by(user_id=user_id, status="active").count()
        eco_points = (
            db.session.query(func.sum(UserChallenge.eco_points_earned)).filter(UserChallenge.user_id == user_id).scalar() or 0
        )
        return jsonify(
            {
                "water_saved_this_month": water_saved_month,
                "active_challenges": active_count,
                "eco_points_earned": eco_points,
            }
        ), 200

    @app.route("/internal/societies/<int:society_id>/impact", methods=["GET"])
    def internal_society_impact(society_id):
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403

        users_payload, status = call_internal_service(
            app.config["AUTH_SERVICE_URL"], "GET", f"/internal/societies/{society_id}/users", expected_status=(200,)
        )
        if status != 200:
            return jsonify({"error": "Auth service unavailable"}), 502
        user_ids = [user["id"] for user in users_payload.get("users", [])]
        if not user_ids:
            return jsonify({"active_initiatives": 0, "water_saved": 0.0, "conservation_impact": {"active": 0, "pending": 0, "completed": 0}}), 200

        water_saved = (
            db.session.query(func.sum(UserChallenge.water_saved)).filter(UserChallenge.user_id.in_(user_ids)).scalar() or 0.0
        )
        active_initiatives = (
            db.session.query(func.count(distinct(UserChallenge.challenge_id)))
            .filter(UserChallenge.user_id.in_(user_ids), UserChallenge.status == "active")
            .scalar()
            or 0
        )
        total_ucs = UserChallenge.query.filter(UserChallenge.user_id.in_(user_ids)).count()
        percs = {"active": 0, "pending": 0, "completed": 0}
        if total_ucs > 0:
            counts = (
                db.session.query(UserChallenge.status, func.count(UserChallenge.status))
                .filter(UserChallenge.user_id.in_(user_ids))
                .group_by(UserChallenge.status)
                .all()
            )
            counts_dict = {status_key: count for status_key, count in counts}
            percs["active"] = (counts_dict.get("active", 0) / total_ucs) * 100
            percs["pending"] = (counts_dict.get("pending", 0) / total_ucs) * 100
            percs["completed"] = (counts_dict.get("completed", 0) / total_ucs) * 100

        return jsonify({"active_initiatives": active_initiatives, "water_saved": water_saved, "conservation_impact": percs}), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
