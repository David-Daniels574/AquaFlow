import json
import logging
import math
import os
import time
import uuid

import psycopg2
import requests
from flask import Flask, g, has_request_context, jsonify, request
from flask_caching import Cache
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity, jwt_required
from prometheus_flask_exporter import PrometheusMetrics
from requests.adapters import HTTPAdapter
from sqlalchemy.exc import OperationalError
from urllib3.util.retry import Retry

try:
    from .models import Supplier, SupplierOffer, TankerListing, db
except ImportError:
    from models import Supplier, SupplierOffer, TankerListing, db


cache = Cache()


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


def haversine_fallback(lat1, lon1, lat2, lon2):
    radius = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return radius * (2 * math.atan2(math.sqrt(value), math.sqrt(1 - value)))


def get_road_metrics(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200 and response.json().get("routes"):
            route = response.json()["routes"][0]
            return route["distance"] / 1000, route["duration"] / 60
    except requests.RequestException:
        pass
    distance = haversine_fallback(lat1, lon1, lat2, lon2)
    eta = (distance / 30) * 60
    return distance, eta


def parse_json_array(value):
    try:
        return json.loads(value) if value else []
    except (TypeError, ValueError):
        return []


def serialize_tanker(tanker, include_private=False):
    images = parse_json_array(tanker.images)
    payload = {
        "id": tanker.id,
        "owner_id": tanker.owner_id,
        "name": f"{tanker.tanker_type} Tanker",
        "vehicle_number": tanker.vehicle_number,
        "capacity": tanker.capacity,
        "type": tanker.tanker_type,
        "price_per_liter": tanker.price_per_liter,
        "base_delivery_fee": tanker.base_delivery_fee,
        "service_areas": parse_json_array(tanker.service_areas),
        "photo_url": images[0] if images else None,
        "images": images,
        "amenities": parse_json_array(tanker.amenities),
        "description": tanker.description,
        "emergency_contact": tanker.emergency_contact,
        "status": tanker.status,
        "is_available": tanker.status == "available",
        "rating": tanker.rating,
        "num_reviews": tanker.total_reviews,
        "total_deliveries": tanker.total_deliveries,
        "area": tanker.area,
        "city": tanker.city,
        "lat": tanker.lat,
        "long": tanker.long,
        "offers": [{"quantity": tanker.capacity, "cost": round((tanker.capacity * tanker.price_per_liter) + tanker.base_delivery_fee, 2)}],
        "starting_from": round((tanker.capacity * tanker.price_per_liter) + tanker.base_delivery_fee, 2),
        "estimated_eta": 45,
        "created_at": tanker.created_at.isoformat() if tanker.created_at else None,
        "updated_at": tanker.updated_at.isoformat() if tanker.updated_at else None,
    }
    if include_private:
        payload["owner_contact"] = tanker.emergency_contact
    return payload


def is_owner_role(role):
    return role in ["tanker_owner", "supplier"]


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

    database_uri = os.environ.get("SUPPLIER_DATABASE_URL") or os.environ.get("DATABASE_URL", "sqlite:///supplier.db")
    if database_uri.startswith("postgres://"):
        database_uri = database_uri.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300
    app.config["INTERNAL_SERVICE_TOKEN"] = os.environ.get("INTERNAL_SERVICE_TOKEN", "internal-dev-token")
    app.config["AUTH_SERVICE_URL"] = os.environ.get("AUTH_SERVICE_URL", "http://auth_service:5000")
    app.config["BOOKING_SERVICE_URL"] = os.environ.get("BOOKING_SERVICE_URL", "http://booking_service:5000")
    app.config["SERVICE_TIMEOUT_SECONDS"] = float(os.environ.get("SERVICE_TIMEOUT_SECONDS", "5"))

    db.init_app(app)
    cache.init_app(app)
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
        app.logger.warning("Database readiness check timed out for supplier_service")

    with app.app_context():
        wait_for_db()
        try:
            db.create_all()
        except OperationalError:
            app.logger.warning("Supplier service tables already created by another worker")

    @app.route("/", methods=["GET"])
    def health():
        return jsonify({"service": "supplier_service", "status": "ok"}), 200

    @app.route("/suppliers", methods=["GET"])
    @jwt_required()
    @cache.cached(timeout=360, key_prefix=lambda: f"suppliers:{get_jwt_identity()}")
    def get_suppliers():
        user_payload, status = call_internal_service(
            app.config["AUTH_SERVICE_URL"],
            "GET",
            f"/internal/users/{int(get_jwt_identity())}",
            expected_status=(200, 404),
        )

        user_lat = user_payload.get("lat") if status == 200 else None
        user_long = user_payload.get("long") if status == 200 else None

        suppliers = Supplier.query.filter_by(verified=True).all()
        response_payload = []
        for supplier in suppliers:
            offers = SupplierOffer.query.filter_by(supplier_id=supplier.id).all()
            distance_km = None
            eta_minutes = None
            if (
                user_lat is not None
                and user_long is not None
                and supplier.lat is not None
                and supplier.long is not None
            ):
                distance_km, eta_minutes = get_road_metrics(user_lat, user_long, supplier.lat, supplier.long)
            response_payload.append(
                {
                    **supplier.to_dict(),
                    "offers": [offer.to_dict() for offer in offers],
                    "starting_from": min([offer.cost for offer in offers]) if offers else None,
                    "distance_km": round(distance_km, 2) if distance_km is not None else None,
                    "estimated_eta": round(eta_minutes, 0) if eta_minutes is not None else None,
                }
            )
        return jsonify(response_payload), 200

    @app.route("/tankers", methods=["GET"])
    @jwt_required()
    def get_tankers():
        tankers = TankerListing.query.order_by(TankerListing.created_at.desc()).all()
        return jsonify([serialize_tanker(tanker) for tanker in tankers]), 200

    @app.route("/tankers", methods=["POST"])
    @jwt_required()
    def create_tanker():
        claims = get_jwt()
        if not is_owner_role(claims.get("role")):
            return jsonify({"error": "Only tanker owners can create listings"}), 403

        data = request.json or {}
        required_fields = ["vehicle_number", "capacity", "price_per_liter"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

        if TankerListing.query.filter_by(vehicle_number=data["vehicle_number"]).first():
            return jsonify({"error": "Vehicle number already exists"}), 400

        tanker = TankerListing(
            owner_id=int(get_jwt_identity()),
            vehicle_number=data["vehicle_number"],
            tanker_type=data.get("type", "Standard"),
            capacity=float(data["capacity"]),
            price_per_liter=float(data["price_per_liter"]),
            base_delivery_fee=float(data.get("base_delivery_fee", 0.0)),
            service_areas=json.dumps(data.get("service_areas", [])),
            images=json.dumps(data.get("images", [])),
            amenities=json.dumps(data.get("amenities", [])),
            description=data.get("description"),
            emergency_contact=data.get("emergency_contact"),
            status=data.get("status", "available"),
            area=data.get("area"),
            city=data.get("city"),
            lat=float(data["lat"]) if data.get("lat") is not None else None,
            long=float(data["long"]) if data.get("long") is not None else None,
        )
        db.session.add(tanker)
        db.session.commit()
        return jsonify({"message": "Tanker listing created", "tanker": serialize_tanker(tanker, include_private=True)}), 201

    @app.route("/tankers/owner", methods=["GET"])
    @jwt_required()
    def owner_tankers():
        claims = get_jwt()
        if not is_owner_role(claims.get("role")):
            return jsonify({"error": "Only tanker owners can access this resource"}), 403
        owner_id = int(get_jwt_identity())
        tankers = TankerListing.query.filter_by(owner_id=owner_id).order_by(TankerListing.created_at.desc()).all()
        return jsonify([serialize_tanker(tanker, include_private=True) for tanker in tankers]), 200

    @app.route("/tankers/<int:tanker_id>", methods=["PUT"])
    @jwt_required()
    def update_tanker(tanker_id):
        tanker = TankerListing.query.get(tanker_id)
        if not tanker:
            return jsonify({"error": "Tanker not found"}), 404
        if tanker.owner_id != int(get_jwt_identity()):
            return jsonify({"error": "Unauthorized"}), 403

        data = request.json or {}
        if "vehicle_number" in data:
            duplicate = TankerListing.query.filter_by(vehicle_number=data["vehicle_number"]).first()
            if duplicate and duplicate.id != tanker_id:
                return jsonify({"error": "Vehicle number already exists"}), 400
            tanker.vehicle_number = data["vehicle_number"]
        if "capacity" in data:
            tanker.capacity = float(data["capacity"])
        if "price_per_liter" in data:
            tanker.price_per_liter = float(data["price_per_liter"])
        if "base_delivery_fee" in data:
            tanker.base_delivery_fee = float(data["base_delivery_fee"])
        if "type" in data:
            tanker.tanker_type = data["type"]
        if "service_areas" in data:
            tanker.service_areas = json.dumps(data["service_areas"])
        if "images" in data:
            tanker.images = json.dumps(data["images"])
        if "amenities" in data:
            tanker.amenities = json.dumps(data["amenities"])
        if "description" in data:
            tanker.description = data["description"]
        if "emergency_contact" in data:
            tanker.emergency_contact = data["emergency_contact"]
        if "status" in data:
            tanker.status = data["status"]
        if "area" in data:
            tanker.area = data["area"]
        if "city" in data:
            tanker.city = data["city"]
        if "lat" in data:
            tanker.lat = float(data["lat"]) if data["lat"] is not None else None
        if "long" in data:
            tanker.long = float(data["long"]) if data["long"] is not None else None

        db.session.commit()
        return jsonify({"message": "Tanker updated", "tanker": serialize_tanker(tanker, include_private=True)}), 200

    @app.route("/tankers/<int:tanker_id>", methods=["DELETE"])
    @jwt_required()
    def delete_tanker(tanker_id):
        tanker = TankerListing.query.get(tanker_id)
        if not tanker:
            return jsonify({"error": "Tanker not found"}), 404
        if tanker.owner_id != int(get_jwt_identity()):
            return jsonify({"error": "Unauthorized"}), 403
        db.session.delete(tanker)
        db.session.commit()
        return jsonify({"message": "Tanker deleted"}), 200

    @app.route("/tankers/<int:tanker_id>/status", methods=["PATCH"])
    @jwt_required()
    def update_tanker_status(tanker_id):
        tanker = TankerListing.query.get(tanker_id)
        if not tanker:
            return jsonify({"error": "Tanker not found"}), 404
        if tanker.owner_id != int(get_jwt_identity()):
            return jsonify({"error": "Unauthorized"}), 403

        status = (request.json or {}).get("status")
        if status not in ["available", "booked", "maintenance"]:
            return jsonify({"error": "Invalid status"}), 400
        tanker.status = status
        db.session.commit()
        return jsonify({"message": "Status updated", "tanker": serialize_tanker(tanker, include_private=True)}), 200

    @app.route("/owner/dashboard", methods=["GET"])
    @jwt_required()
    def owner_dashboard():
        claims = get_jwt()
        if not is_owner_role(claims.get("role")):
            return jsonify({"error": "Only tanker owners can access this resource"}), 403

        owner_id = int(get_jwt_identity())
        tankers = TankerListing.query.filter_by(owner_id=owner_id).all()
        dashboard_data, status = call_internal_service(
            app.config["BOOKING_SERVICE_URL"],
            "GET",
            f"/internal/owners/{owner_id}/dashboard",
            expected_status=(200,),
        )
        if status != 200:
            return jsonify({"error": "Booking service unavailable for dashboard"}), 502

        avg_rating = round(sum((tanker.rating or 0) for tanker in tankers) / len(tankers), 2) if tankers else 0.0
        return jsonify(
            {
                "total_tankers": len(tankers),
                "average_rating": avg_rating,
                "active_bookings": dashboard_data.get("active_bookings", 0),
                "this_month_earnings": dashboard_data.get("this_month_earnings", 0),
                "pending_bookings": dashboard_data.get("pending_bookings", 0),
                "recent_activity": dashboard_data.get("recent_activity", []),
            }
        ), 200

    @app.route("/owner/earnings", methods=["GET"])
    @jwt_required()
    def owner_earnings():
        claims = get_jwt()
        if not is_owner_role(claims.get("role")):
            return jsonify({"error": "Only tanker owners can access this resource"}), 403

        owner_id = int(get_jwt_identity())
        earnings_data, status = call_internal_service(
            app.config["BOOKING_SERVICE_URL"],
            "GET",
            f"/internal/owners/{owner_id}/earnings",
            expected_status=(200,),
        )
        if status != 200:
            return jsonify({"error": "Booking service unavailable for earnings"}), 502

        owner_tankers = TankerListing.query.filter_by(owner_id=owner_id).all()
        tanker_map = {tanker.id: tanker.vehicle_number for tanker in owner_tankers}
        by_tanker = []
        for row in earnings_data.get("by_tanker", []):
            by_tanker.append(
                {
                    "tanker_id": row["tanker_id"],
                    "vehicle_number": tanker_map.get(row["tanker_id"], row.get("vehicle_number", "Unknown")),
                    "amount": row["amount"],
                }
            )

        return jsonify(
            {
                "total_earnings": earnings_data.get("total_earnings", 0),
                "completed_orders": earnings_data.get("completed_orders", 0),
                "monthly": earnings_data.get("monthly", []),
                "by_tanker": by_tanker,
            }
        ), 200

    @app.route("/internal/tankers/<int:tanker_id>", methods=["GET"])
    def internal_tanker_details(tanker_id):
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403
        tanker = TankerListing.query.get(tanker_id)
        if not tanker:
            return jsonify({"error": "Tanker not found"}), 404
        return jsonify(serialize_tanker(tanker, include_private=True)), 200

    @app.route("/internal/tankers/<int:tanker_id>/status", methods=["PATCH"])
    def internal_update_tanker_status(tanker_id):
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403
        tanker = TankerListing.query.get(tanker_id)
        if not tanker:
            return jsonify({"error": "Tanker not found"}), 404
        status = (request.json or {}).get("status")
        if status not in ["available", "booked", "maintenance"]:
            return jsonify({"error": "Invalid status"}), 400
        tanker.status = status
        db.session.commit()
        return jsonify({"message": "Status updated"}), 200

    @app.route("/internal/suppliers/<int:supplier_id>", methods=["GET"])
    def internal_supplier_details(supplier_id):
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({"error": "Supplier not found"}), 404
        return jsonify(supplier.to_dict()), 200

    @app.route("/internal/suppliers/batch", methods=["POST"])
    def internal_supplier_batch():
        if not require_internal_auth():
            return jsonify({"error": "Unauthorized internal request"}), 403
        supplier_ids = (request.json or {}).get("supplier_ids", [])
        if not isinstance(supplier_ids, list):
            return jsonify({"error": "supplier_ids must be a list"}), 400
        suppliers = Supplier.query.filter(Supplier.id.in_(supplier_ids)).all() if supplier_ids else []
        return jsonify({"suppliers": [supplier.to_dict() for supplier in suppliers]}), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
