import logging
import os
import time
import uuid
from datetime import datetime, timedelta

import psycopg2
import requests
from flask import Flask, g, has_request_context, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required
from prometheus_flask_exporter import PrometheusMetrics
from requests.adapters import HTTPAdapter
from sqlalchemy import extract, func
from sqlalchemy.exc import OperationalError
from urllib3.util.retry import Retry

try:
    from .models import UserDailyUsage, WaterReading, db
except ImportError:
    from models import UserDailyUsage, WaterReading, db


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

    database_uri = os.environ.get("IOT_DATABASE_URL") or os.environ.get("DATABASE_URL", "sqlite:///iot.db")
    if database_uri.startswith("postgres://"):
        database_uri = database_uri.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["INTERNAL_SERVICE_TOKEN"] = os.environ.get("INTERNAL_SERVICE_TOKEN", "internal-dev-token")
    app.config["AUTH_SERVICE_URL"] = os.environ.get("AUTH_SERVICE_URL", "http://auth_service:5000")
    app.config["BOOKING_SERVICE_URL"] = os.environ.get("BOOKING_SERVICE_URL", "http://booking_service:5000")
    app.config["GAMIFICATION_SERVICE_URL"] = os.environ.get("GAMIFICATION_SERVICE_URL", "http://gamification_service:5000")
    app.config["SUPPLIER_SERVICE_URL"] = os.environ.get("SUPPLIER_SERVICE_URL", "http://supplier_service:5000")
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
        if status != 200:
            return None
        return payload

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
        app.logger.warning("Database readiness check timed out for iot_analytics_service")

    with app.app_context():
        wait_for_db()
        try:
            db.create_all()
        except OperationalError:
            app.logger.warning("IoT service tables already created by another worker")

    @app.route("/", methods=["GET"])
    def health():
        return jsonify({"service": "iot_analytics_service", "status": "ok"}), 200

    @app.route("/ping", methods=["GET"])
    def ping():
        return jsonify({"message": "pong", "service": "iot_analytics_service"}), 200

    @app.route("/log_reading", methods=["POST"])
    @jwt_required()
    def log_reading():
        user_id = int(get_jwt_identity())
        user = get_user_context(user_id)
        if not user:
            return jsonify({"error": "User not found in auth service"}), 404

        data = request.json or {}
        if "reading" not in data:
            return jsonify({"error": "Missing fields: reading"}), 400

        try:
            reading_value = float(data["reading"])
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid reading value"}), 400

        timestamp = datetime.utcnow()
        if "timestamp" in data:
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except ValueError:
                return jsonify({"error": "Invalid timestamp format"}), 400

        row = WaterReading(
            user_id=user_id,
            reading=reading_value,
            society_id=user.get("society_id"),
            timestamp=timestamp,
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({"message": "Reading logged"}), 201

    @app.route("/consumption_report", methods=["GET"])
    @jwt_required()
    def consumption_report():
        user_id = int(get_jwt_identity())
        period = request.args.get("period", "daily")
        now = datetime.utcnow()
        if period == "weekly":
            start_dt = now - timedelta(days=7)
        elif period == "monthly":
            start_dt = now - timedelta(days=30)
        else:
            start_dt = now - timedelta(days=1)

        rows = (
            WaterReading.query.filter(WaterReading.user_id == user_id, WaterReading.timestamp >= start_dt)
            .order_by(WaterReading.timestamp)
            .all()
        )
        if not rows:
            return jsonify({"period": period, "total_usage_liters": 0, "daily_breakdown": []}), 200

        day_bounds = {}
        for row in rows:
            day_key = row.timestamp.date().isoformat()
            if day_key not in day_bounds:
                day_bounds[day_key] = {"first": row.reading, "last": row.reading}
            else:
                day_bounds[day_key]["last"] = row.reading

        total_usage = 0.0
        daily_breakdown = []
        for day in sorted(day_bounds.keys()):
            usage = max(day_bounds[day]["last"] - day_bounds[day]["first"], 0.0)
            usage = round(usage, 2)
            total_usage += usage
            daily_breakdown.append({"date": day, "usage": usage})

        return jsonify({"period": period, "total_usage_liters": round(total_usage, 2), "daily_breakdown": daily_breakdown}), 200

    @app.route("/conservation_summary", methods=["GET"])
    @jwt_required()
    def conservation_summary():
        user_id = int(get_jwt_identity())
        summary, status = call_internal_service(
            app.config["GAMIFICATION_SERVICE_URL"],
            "GET",
            f"/internal/users/{user_id}/summary",
            expected_status=(200,),
        )
        if status != 200:
            return jsonify({"error": "Gamification service unavailable"}), 502
        return jsonify(summary), 200

    @app.route("/society_dashboard", methods=["GET"])
    @jwt_required()
    def society_dashboard():
        user = get_user_context(int(get_jwt_identity()))
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.get("society_id") is None:
            return jsonify({"message": "No society associated"}), 200

        society_id = int(user["society_id"])
        current_year = datetime.utcnow().year

        monthly_data = (
            db.session.query(
                extract("month", UserDailyUsage.date).label("month"),
                func.sum(UserDailyUsage.total_usage_liters).label("total_consumption"),
            )
            .filter(
                UserDailyUsage.society_id == society_id,
                extract("year", UserDailyUsage.date) == current_year,
            )
            .group_by(extract("month", UserDailyUsage.date))
            .all()
        )

        monthly_consumption = {int(row.month): row.total_consumption for row in monthly_data}
        for month in range(1, 13):
            monthly_consumption.setdefault(month, 0.0)

        orders_summary, booking_status = call_internal_service(
            app.config["BOOKING_SERVICE_URL"],
            "GET",
            f"/internal/societies/{society_id}/orders-summary",
            expected_status=(200,),
        )
        if booking_status != 200:
            return jsonify({"error": "Booking service unavailable"}), 502

        impact_summary, impact_status = call_internal_service(
            app.config["GAMIFICATION_SERVICE_URL"],
            "GET",
            f"/internal/societies/{society_id}/impact",
            expected_status=(200,),
        )
        if impact_status != 200:
            return jsonify({"error": "Gamification service unavailable"}), 502

        deliveries = orders_summary.get("scheduled_deliveries", [])
        supplier_ids = sorted({delivery["supplier_id"] for delivery in deliveries})
        supplier_payload, supplier_status = call_internal_service(
            app.config["SUPPLIER_SERVICE_URL"],
            "POST",
            "/internal/suppliers/batch",
            payload={"supplier_ids": supplier_ids},
            expected_status=(200,),
        )
        if supplier_status != 200:
            return jsonify({"error": "Supplier service unavailable"}), 502
        supplier_lookup = {supplier["id"]: supplier for supplier in supplier_payload.get("suppliers", [])}

        scheduled_deliveries = []
        for delivery in deliveries:
            supplier = supplier_lookup.get(delivery["supplier_id"], {})
            scheduled_deliveries.append(
                {
                    "supplier": supplier.get("name", "Unknown"),
                    "date": delivery.get("date"),
                    "time": delivery.get("time"),
                    "volume": delivery.get("volume"),
                    "status": delivery.get("status"),
                }
            )

        return jsonify(
            {
                "monthly_consumption": monthly_consumption,
                "tankers_ordered_ytd": orders_summary.get("tankers_ordered_ytd", 0),
                "total_volume_ytd": orders_summary.get("total_volume_ytd", 0),
                "active_initiatives": impact_summary.get("active_initiatives", 0),
                "water_saved": impact_summary.get("water_saved", 0),
                "conservation_impact": impact_summary.get(
                    "conservation_impact", {"active": 0, "pending": 0, "completed": 0}
                ),
                "scheduled_deliveries": scheduled_deliveries,
            }
        ), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
