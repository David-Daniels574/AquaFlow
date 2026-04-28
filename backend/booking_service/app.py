import logging
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime

import psycopg2
import requests
import stripe
from flask import Flask, g, has_request_context, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity, jwt_required
from prometheus_flask_exporter import PrometheusMetrics
from requests.adapters import HTTPAdapter
from sqlalchemy.exc import OperationalError
from urllib3.util.retry import Retry

try:
    from .models import TankerBooking, TankerOrder, db
except ImportError:
    from models import TankerBooking, TankerOrder, db


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

    database_uri = os.environ.get("BOOKING_DATABASE_URL") or os.environ.get("DATABASE_URL", "sqlite:///booking.db")
    if database_uri.startswith("postgres://"):
        database_uri = database_uri.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["INTERNAL_SERVICE_TOKEN"] = os.environ.get("INTERNAL_SERVICE_TOKEN", "internal-dev-token")
    app.config["AUTH_SERVICE_URL"] = os.environ.get("AUTH_SERVICE_URL", "http://auth_service:5000")
    app.config["SUPPLIER_SERVICE_URL"] = os.environ.get("SUPPLIER_SERVICE_URL", "http://supplier_service:5000")
    app.config["SERVICE_TIMEOUT_SECONDS"] = float(os.environ.get("SERVICE_TIMEOUT_SECONDS", "5"))

    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

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
        app.logger.warning("Database readiness check timed out for booking_service")

    with app.app_context():
        wait_for_db()
        try:
            db.create_all()
        except OperationalError:
            app.logger.warning("Booking service tables already created by another worker")

    @app.route("/", methods=["GET"])
    def health():
        return jsonify({"service": "booking_service", "status": "ok"}), 200

    @app.route("/ping", methods=["GET"])
    def ping():
        return jsonify({"message": "pong", "service": "booking_service"}), 200

    @app.route("/book_tanker", methods=["POST"])
    @jwt_required()
    def book_tanker():
        data = request.json or {}
        required_fields = ["supplier_id", "volume", "price"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        supplier_id = int(data["supplier_id"])
        supplier_payload, status = call_internal_service(
            app.config["SUPPLIER_SERVICE_URL"], "GET", f"/internal/suppliers/{supplier_id}", expected_status=(200, 404)
        )
        if status == 404:
            return jsonify({"error": "Supplier not found"}), 404
        if status != 200:
            return jsonify({"error": "Supplier service unavailable"}), 502

        order = TankerOrder(
            user_id=int(get_jwt_identity()),
            supplier_id=supplier_id,
            volume=float(data["volume"]),
            price=float(data["price"]),
            status="pending",
            society_id=data.get("society_id") or get_jwt().get("society_id"),
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({"message": "Order placed", "order_id": order.id, "supplier_name": supplier_payload.get("name")}), 201

    @app.route("/track_order/<int:order_id>", methods=["GET"])
    @jwt_required()
    def track_order(order_id):
        order = TankerOrder.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        return jsonify(
            {
                "status": order.status,
                "lat": order.tracking_lat,
                "long": order.tracking_long,
                "delivery_time": order.delivery_time.isoformat() if order.delivery_time else None,
            }
        ), 200

    @app.route("/update_order/<int:order_id>", methods=["PUT"])
    @jwt_required()
    def update_order(order_id):
        claims = get_jwt()
        if claims.get("role") != "supplier":
            return jsonify({"error": "Unauthorized"}), 403

        order = TankerOrder.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404

        data = request.json or {}
        if "status" in data:
            order.status = data["status"]
        if "lat" in data:
            order.tracking_lat = float(data["lat"])
        if "long" in data:
            order.tracking_long = float(data["long"])
        if "delivery_time" in data:
            try:
                order.delivery_time = datetime.fromisoformat(data["delivery_time"])
            except ValueError:
                return jsonify({"error": "Invalid delivery_time format"}), 400
        db.session.commit()
        return jsonify({"message": "Order updated"}), 200

    @app.route("/bookings", methods=["POST"])
    @jwt_required()
    def create_booking():
        data = request.json or {}
        required_fields = ["tanker_id", "quantity", "total_amount"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        tanker_id = int(data["tanker_id"])
        tanker_payload, status = call_internal_service(
            app.config["SUPPLIER_SERVICE_URL"], "GET", f"/internal/tankers/{tanker_id}", expected_status=(200, 404)
        )
        if status == 404:
            return jsonify({"error": "Tanker not found"}), 404
        if status != 200:
            return jsonify({"error": "Supplier service unavailable"}), 502
        if tanker_payload.get("status") != "available":
            return jsonify({"error": "Tanker is not available"}), 400

        status_payload, update_status = call_internal_service(
            app.config["SUPPLIER_SERVICE_URL"],
            "PATCH",
            f"/internal/tankers/{tanker_id}/status",
            payload={"status": "booked"},
            expected_status=(200,),
        )
        if update_status != 200:
            return jsonify({"error": "Failed to lock tanker for booking"}), 502

        try:
            booking = TankerBooking(
                tanker_id=tanker_id,
                owner_id=int(tanker_payload["owner_id"]),
                tanker_vehicle_number=tanker_payload.get("vehicle_number"),
                customer_id=int(get_jwt_identity()),
                delivery_address=data.get("delivery_address", "Address to be shared on confirmation"),
                delivery_pincode=data.get("delivery_pincode"),
                quantity=float(data["quantity"]),
                total_amount=float(data["total_amount"]),
                status="pending",
                scheduled_time=datetime.fromisoformat(data["scheduled_time"]) if data.get("scheduled_time") else None,
            )
            db.session.add(booking)
            db.session.commit()
            return jsonify({"message": "Booking created", "booking_id": booking.id}), 201
        except Exception as exc:
            db.session.rollback()
            app.logger.error("Booking creation failed, rolling tanker status back: %s", exc)
            call_internal_service(
                app.config["SUPPLIER_SERVICE_URL"],
                "PATCH",
                f"/internal/tankers/{tanker_id}/status",
                payload={"status": "available"},
                expected_status=(200,),
            )
            return jsonify({"error": "Failed to create booking"}), 500

    @app.route("/bookings/owner", methods=["GET"])
    @jwt_required()
    def owner_bookings():
        claims = get_jwt()
        if claims.get("role") not in ["tanker_owner", "supplier"]:
            return jsonify({"error": "Only tanker owners can access this resource"}), 403

        owner_id = int(get_jwt_identity())
        bookings = TankerBooking.query.filter_by(owner_id=owner_id).order_by(TankerBooking.created_at.desc()).all()
        customer_ids = sorted({booking.customer_id for booking in bookings})
        users_payload, status = call_internal_service(
            app.config["AUTH_SERVICE_URL"],
            "POST",
            "/internal/users/batch",
            payload={"user_ids": customer_ids},
            expected_status=(200,),
        )
        if status != 200:
            return jsonify({"error": "Auth service unavailable for customer details"}), 502
        user_lookup = {user["id"]: user for user in users_payload.get("users", [])}

        response_payload = []
        for booking in bookings:
            customer = user_lookup.get(booking.customer_id, {})
            response_payload.append(
                {
                    "id": booking.id,
                    "tanker_id": booking.tanker_id,
                    "tanker_vehicle_number": booking.tanker_vehicle_number,
                    "customer": {
                        "id": booking.customer_id,
                        "username": customer.get("username", "Unknown"),
                        "email": customer.get("email"),
                    },
                    "delivery_address": booking.delivery_address,
                    "delivery_pincode": booking.delivery_pincode,
                    "quantity": booking.quantity,
                    "total_amount": booking.total_amount,
                    "status": booking.status,
                    "scheduled_time": booking.scheduled_time.isoformat() if booking.scheduled_time else None,
                    "delivered_time": booking.delivered_time.isoformat() if booking.delivered_time else None,
                    "created_at": booking.created_at.isoformat() if booking.created_at else None,
                }
            )
        return jsonify(response_payload), 200

    @app.route("/bookings/<int:booking_id>/status", methods=["PATCH"])
    @jwt_required()
    def update_booking_status(booking_id):
        booking = TankerBooking.query.get(booking_id)
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking.owner_id != int(get_jwt_identity()):
            return jsonify({"error": "Unauthorized"}), 403

        status = (request.json or {}).get("status")
        if status not in ["pending", "confirmed", "in_transit", "completed", "cancelled"]:
            return jsonify({"error": "Invalid status"}), 400

        booking.status = status
        if status == "completed":
            booking.delivered_time = datetime.utcnow()
        db.session.commit()

        if status in ["cancelled", "completed"]:
            _, supplier_status = call_internal_service(
                app.config["SUPPLIER_SERVICE_URL"],
                "PATCH",
                f"/internal/tankers/{booking.tanker_id}/status",
                payload={"status": "available"},
                expected_status=(200,),
            )
            if supplier_status != 200:
                return jsonify({"error": "Booking updated but tanker status sync failed"}), 502

        return jsonify({"message": "Booking status updated"}), 200

    @app.route("/society_bulk_order", methods=["POST"])
    @jwt_required()
    def society_bulk_order():
        claims = get_jwt()
        if claims.get("role") != "society_admin":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.json or {}
        required_fields = ["supplier_id", "volume", "price", "society_id"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        supplier_id = int(data["supplier_id"])
        _, status = call_internal_service(
            app.config["SUPPLIER_SERVICE_URL"], "GET", f"/internal/suppliers/{supplier_id}", expected_status=(200, 404)
        )
        if status == 404:
            return jsonify({"error": "Supplier not found"}), 404
        if status != 200:
            return jsonify({"error": "Supplier service unavailable"}), 502

        order = TankerOrder(
            user_id=int(get_jwt_identity()),
            supplier_id=supplier_id,
            society_id=int(data["society_id"]),
            volume=float(data["volume"]),
            price=float(data["price"]),
            status="pending",
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({"message": "Bulk order placed", "order_id": order.id}), 201

    @app.route("/create-payment-intent", methods=["POST"])
    @jwt_required()
    def create_payment_intent():
        data = request.json or {}
        if not data.get("amount") or not data.get("booking_id"):
            return jsonify({"error": "Missing required fields: amount and booking_id"}), 400
        try:
            amount = float(data["amount"])
        except ValueError:
            return jsonify({"error": "Invalid amount format"}), 400
        if amount <= 40:
            return jsonify({"error": "Invalid amount"}), 400
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency="inr",
                payment_method_types=["card"],
                metadata={"booking_id": str(data["booking_id"]), "user_id": str(get_jwt_identity())},
            )
            return jsonify({"clientSecret": intent.client_secret}), 200
        except Exception:
            return jsonify({"error": "Failed to create payment intent"}), 500

    @app.route("/internal/owners/<int:owner_id>/dashboard", methods=["GET"])
    def internal_owner_dashboard(owner_id):
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403
        bookings = TankerBooking.query.filter_by(owner_id=owner_id).all()
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        active_bookings = sum(1 for booking in bookings if booking.status in ["pending", "confirmed", "in_transit"])
        pending_bookings = sum(1 for booking in bookings if booking.status == "pending")
        month_earnings = sum(
            booking.total_amount
            for booking in bookings
            if booking.status == "completed" and booking.delivered_time and booking.delivered_time >= month_start
        )
        recent = sorted(bookings, key=lambda item: item.created_at or datetime.min, reverse=True)[:6]
        recent_activity = [
            {
                "booking_id": booking.id,
                "tanker_id": booking.tanker_id,
                "status": booking.status,
                "total_amount": booking.total_amount,
                "quantity": booking.quantity,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
            }
            for booking in recent
        ]
        return jsonify(
            {
                "active_bookings": active_bookings,
                "pending_bookings": pending_bookings,
                "this_month_earnings": round(month_earnings, 2),
                "recent_activity": recent_activity,
            }
        ), 200

    @app.route("/internal/owners/<int:owner_id>/earnings", methods=["GET"])
    def internal_owner_earnings(owner_id):
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403
        completed = TankerBooking.query.filter_by(owner_id=owner_id, status="completed").all()
        total_earnings = round(sum(booking.total_amount for booking in completed), 2)
        completed_orders = len(completed)

        monthly = defaultdict(float)
        by_tanker = defaultdict(float)
        for booking in completed:
            date_key = (booking.delivered_time or booking.created_at).strftime("%Y-%m")
            monthly[date_key] += booking.total_amount
            by_tanker[booking.tanker_id] += booking.total_amount

        return jsonify(
            {
                "total_earnings": total_earnings,
                "completed_orders": completed_orders,
                "monthly": [{"month": month, "amount": round(amount, 2)} for month, amount in sorted(monthly.items())],
                "by_tanker": [
                    {
                        "tanker_id": tanker_id,
                        "vehicle_number": "Unknown",
                        "amount": round(amount, 2),
                    }
                    for tanker_id, amount in by_tanker.items()
                ],
            }
        ), 200

    @app.route("/internal/societies/<int:society_id>/orders-summary", methods=["GET"])
    def internal_society_orders_summary(society_id):
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403

        current_year = datetime.utcnow().year
        y_start = datetime(current_year, 1, 1)
        orders = TankerOrder.query.filter(TankerOrder.society_id == society_id, TankerOrder.order_time >= y_start).all()
        pending_orders = TankerOrder.query.filter(
            TankerOrder.society_id == society_id, TankerOrder.status.in_(["pending", "en_route"])
        ).all()

        return jsonify(
            {
                "tankers_ordered_ytd": len(orders),
                "total_volume_ytd": sum(order.volume for order in orders),
                "scheduled_deliveries": [
                    {
                        "supplier_id": order.supplier_id,
                        "date": order.delivery_time.date().isoformat() if order.delivery_time else None,
                        "time": order.delivery_time.time().isoformat() if order.delivery_time else None,
                        "volume": order.volume,
                        "status": order.status,
                    }
                    for order in pending_orders
                ],
            }
        ), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
