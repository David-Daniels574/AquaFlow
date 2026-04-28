import logging
import os
import time
import uuid

import psycopg2
from flask import Flask, g, has_request_context, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from prometheus_flask_exporter import PrometheusMetrics
from sqlalchemy.exc import IntegrityError, OperationalError

try:
    from .models import Society, User, db
except ImportError:
    from models import Society, User, db


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


def normalize_role(role: str) -> str:
    role_map = {
        "customer": "user",
        "user": "user",
        "tanker_owner": "tanker_owner",
        "supplier": "supplier",
        "admin": "society_admin",
        "society_admin": "society_admin",
    }
    return role_map.get((role or "").strip().lower(), "user")


def create_app():
    configure_logging()
    app = Flask(__name__)

    database_uri = os.environ.get("AUTH_DATABASE_URL") or os.environ.get("DATABASE_URL", "sqlite:///auth.db")
    if database_uri.startswith("postgres://"):
        database_uri = database_uri.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["INTERNAL_SERVICE_TOKEN"] = os.environ.get("INTERNAL_SERVICE_TOKEN", "internal-dev-token")

    db.init_app(app)
    CORS(app)
    JWTManager(app)
    PrometheusMetrics(app)

    @app.before_request
    def attach_correlation_id():
        g.correlation_id = request.headers.get("X-Correlation-ID") or f"req-{uuid.uuid4().hex[:12]}"

    @app.after_request
    def add_correlation_header(response):
        response.headers["X-Correlation-ID"] = g.correlation_id
        return response

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
        app.logger.warning("Database readiness check timed out for auth_service")

    with app.app_context():
        wait_for_db()
        try:
            db.create_all()
        except OperationalError:
            app.logger.warning("Auth service tables already created by another worker")

    def require_internal_auth():
        token = request.headers.get("X-Internal-Service-Token")
        if token != app.config["INTERNAL_SERVICE_TOKEN"]:
            return False
        return True

    @app.route("/", methods=["GET"])
    def health():
        return jsonify({"service": "auth_service", "status": "ok"}), 200

    @app.route("/ping", methods=["GET"])
    def ping():
        return jsonify({"message": "pong", "service": "auth_service"}), 200

    @app.route("/register", methods=["POST"])
    def register():
        data = request.json or {}
        required_fields = ["username", "email", "password", "role"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        if User.query.filter((User.username == data["username"]) | (User.email == data["email"])).first():
            return jsonify({"error": "User already exists"}), 400

        user = User(
            username=data["username"],
            email=data["email"],
            role=normalize_role(data.get("role")),
            society_id=data.get("society_id"),
            area=data.get("area"),
            city=data.get("city"),
            lat=data.get("lat"),
            long=data.get("long"),
        )
        user.set_password(data["password"])

        try:
            db.session.add(user)
            db.session.commit()
            return jsonify({"message": "User registered successfully", "user_id": user.id}), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "User already exists"}), 400

    @app.route("/login", methods=["POST"])
    def login():
        data = request.json or {}
        required_fields = ["identifier", "password"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        identifier = data["identifier"]
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
        if not user or not user.check_password(data["password"]):
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role, "society_id": user.society_id},
        )
        return jsonify({"access_token": token}), 200

    @app.route("/profile", methods=["GET", "PUT"])
    @jwt_required()
    def profile():
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if request.method == "PUT":
            data = request.json or {}
            if "area" in data:
                user.area = data["area"]
            if "city" in data:
                user.city = data["city"]
            if "lat" in data:
                user.lat = float(data["lat"]) if data["lat"] is not None else None
            if "long" in data:
                user.long = float(data["long"]) if data["long"] is not None else None
            if "society_id" in data:
                user.society_id = data["society_id"]

            db.session.commit()
            return jsonify({"message": "Profile updated successfully"}), 200

        society = Society.query.get(user.society_id) if user.society_id else None
        return jsonify(
            {
                "personal_info": {
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
                "location_info": {
                    "area": user.area,
                    "city": user.city,
                    "coordinates": {"lat": user.lat, "long": user.long},
                },
                "society_info": {
                    "id": user.society_id,
                    "name": society.name if society else "Not Assigned",
                    "address": society.address if society else None,
                },
            }
        ), 200

    @app.route("/internal/users/<int:user_id>", methods=["GET"])
    def internal_user(user_id):
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user.to_dict()), 200

    @app.route("/internal/users/batch", methods=["POST"])
    def internal_users_batch():
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403
        data = request.json or {}
        user_ids = data.get("user_ids", [])
        if not isinstance(user_ids, list):
            return jsonify({"error": "user_ids must be a list"}), 400
        users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
        return jsonify({"users": [u.to_dict() for u in users]}), 200

    @app.route("/internal/societies/<int:society_id>/users", methods=["GET"])
    def internal_society_users(society_id):
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403
        users = User.query.filter_by(society_id=society_id).all()
        return jsonify({"users": [u.to_dict() for u in users]}), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
