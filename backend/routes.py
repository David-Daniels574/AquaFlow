from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import UserDailyUsage, db, User, Supplier, TankerOrder, WaterReading, ConservationTip, Society, SupplierOffer, Challenge, UserChallenge, Broadcast, DiscussionThread, ThreadComment, TankerListing, TankerBooking
from auth import register_user, login_user
from utils import get_consumption_reports, calculate_eta, get_road_metrics
from datetime import datetime, timedelta
from collections import defaultdict
import stripe 
from dotenv import load_dotenv
import os
import json
from sqlalchemy import func, distinct , extract
from app import cache,db

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

api = Blueprint('api', __name__)


def _is_owner_role(role):
    return role in ['tanker_owner', 'supplier']


def _serialize_tanker(tanker, include_private=False):
    try:
        service_areas = json.loads(tanker.service_areas) if tanker.service_areas else []
    except Exception:
        service_areas = []

    try:
        images = json.loads(tanker.images) if tanker.images else []
    except Exception:
        images = []

    try:
        amenities = json.loads(tanker.amenities) if tanker.amenities else []
    except Exception:
        amenities = []

    payload = {
        'id': tanker.id,
        'owner_id': tanker.owner_id,
        'name': f"{tanker.tanker_type} Tanker",
        'vehicle_number': tanker.vehicle_number,
        'capacity': tanker.capacity,
        'type': tanker.tanker_type,
        'price_per_liter': tanker.price_per_liter,
        'base_delivery_fee': tanker.base_delivery_fee,
        'service_areas': service_areas,
        'photo_url': images[0] if images else None,
        'images': images,
        'amenities': amenities,
        'description': tanker.description,
        'emergency_contact': tanker.emergency_contact,
        'status': tanker.status,
        'is_available': tanker.status == 'available',
        'rating': tanker.rating,
        'num_reviews': tanker.total_reviews,
        'total_deliveries': tanker.total_deliveries,
        'area': tanker.area,
        'city': tanker.city,
        'lat': tanker.lat,
        'long': tanker.long,
        'offers': [{
            'quantity': tanker.capacity,
            'cost': round((tanker.capacity * tanker.price_per_liter) + tanker.base_delivery_fee, 2)
        }],
        'starting_from': round((tanker.capacity * tanker.price_per_liter) + tanker.base_delivery_fee, 2),
        'estimated_eta': 45,
        'created_at': tanker.created_at.isoformat() if tanker.created_at else None,
        'updated_at': tanker.updated_at.isoformat() if tanker.updated_at else None,
    }

    if include_private:
        payload['owner_contact'] = tanker.emergency_contact

    return payload

@api.route('/', methods=['GET'])
def home():
    return "<h1>Hello! Backend is ONLINE.</h1>", 200

@api.route('/ping', methods=['GET'])
def ping():
    return jsonify({
        "status": "success",
        "message": "Pong! The container is reachable.",
        "port": 5000
    }), 200


@api.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    """
    data = request.json
    required_fields = ['username', 'email', 'password', 'role']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    
    user, error = register_user(
        data['username'], data['email'], data['password'], data['role'], data.get('society_id'),
        data.get('area'), data.get('city'), data.get('lat'), data.get('long')
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'message': 'User registered successfully'}), 201

@api.route('/login', methods=['POST'])
def login():
    """
    Login and retrieve JWT token.
    """
    data = request.json
    required_fields = ['identifier', 'password']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    
    token, error = login_user(data['identifier'], data['password'])
    if error:
        return jsonify({'error': error}), 401
    return jsonify({'access_token': token}), 200

@api.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
def profile():
    """
    GET  -> Fetch comprehensive user profile (for UI display)
    PUT  -> Update editable profile fields
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # -------------------------
    # UPDATE PROFILE (PUT)
    # -------------------------
    if request.method == 'PUT':
        data = request.json or {}
        updated = False

        if 'area' in data:
            user.area = data['area']
            updated = True

        if 'city' in data:
            user.city = data['city']
            updated = True

        if 'lat' in data:
            user.lat = float(data['lat'])
            updated = True

        if 'long' in data:
            user.long = float(data['long'])
            updated = True

        if not updated:
            return jsonify({'message': 'No updates provided'}), 200

        try:
            db.session.commit()
            return jsonify({'message': 'Profile updated successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # -------------------------
    # FETCH PROFILE (GET)
    # -------------------------
    society_name = "Not Assigned"
    society_address = None

    if user.society_id:
        society = Society.query.get(user.society_id)
        if society:
            society_name = society.name
            society_address = society.address

    return jsonify({
        'personal_info': {
            'username': user.username,
            'email': user.email,
            'role': user.role
        },
        'location_info': {
            'area': user.area,
            'city': user.city,
            'coordinates': {
                'lat': user.lat,
                'long': user.long
            }
        },
        'society_info': {
            'id': user.society_id,
            'name': society_name,
            'address': society_address
        }
    }), 200

@api.route('/suppliers', methods=['GET'])
@jwt_required()
@cache.cached(timeout=360, key_prefix=lambda: f"suppliers:{get_jwt_identity()}")
def get_suppliers():
    """
    Get list of verified suppliers with details.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    suppliers = Supplier.query.filter_by(verified=True).all()
    suppliers_list = []
    for s in suppliers:
        offers = SupplierOffer.query.filter_by(supplier_id=s.id).all()
        offer_data = [{'quantity': o.quantity, 'cost': o.cost} for o in offers]
        min_cost = min([o.cost for o in offers]) if offers else None
        eta = None
        if user and user.lat is not None and user.long is not None and s.lat is not None and s.long is not None:
            distance, eta = get_road_metrics(user.lat, user.long, s.lat, s.long)
        suppliers_list.append({
            'id': s.id,
            'name': s.name,
            'contact': s.contact,
            'photo_url': s.photo_url,
            'area': s.area,
            'city': s.city,
            'rating': s.rating,
            'num_reviews': s.num_reviews,
            'lat': s.lat,
            'long': s.long,
            'offers': offer_data,
            'starting_from': min_cost,
            'distance_km': round(distance, 2), 
            'estimated_eta': round(eta, 0)
        })
    return jsonify(suppliers_list), 200

@api.route('/book_tanker', methods=['POST'])
@jwt_required()
def book_tanker():
    """
    Book a water tanker.
    """
    user_id = int(get_jwt_identity())
    data = request.json
    required_fields = ['supplier_id', 'volume', 'price']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    
    try:
        supplier_id = int(data['supplier_id'])
        volume = float(data['volume'])
        price = float(data['price'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid data types'}), 400
    
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return jsonify({'error': 'Supplier not found'}), 404
    
    order = TankerOrder(
        user_id=user_id,
        supplier_id=supplier_id,
        volume=volume,
        price=price,
        status='pending',
        society_id=data.get('society_id')
    )
    try:
        db.session.add(order)
        db.session.commit()
        return jsonify({'message': 'Order placed', 'order_id': order.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/track_order/<int:order_id>', methods=['GET'])
@jwt_required()
def track_order(order_id):
    """
    Track a tanker order.
    """
    order = TankerOrder.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({
        'status': order.status,
        'lat': order.tracking_lat,
        'long': order.tracking_long,
        'delivery_time': order.delivery_time.isoformat() if order.delivery_time else None
    }), 200

@api.route('/update_order/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    """
    Update tanker order (supplier only).
    """
    claims = get_jwt()
    if claims.get('role') != 'supplier':
        return jsonify({'error': 'Unauthorized'}), 403
    
    order = TankerOrder.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    data = request.json
    if 'status' in data:
        order.status = data['status']
    if 'lat' in data:
        order.tracking_lat = float(data['lat'])
    if 'long' in data:
        order.tracking_long = float(data['long'])
    if 'delivery_time' in data:
        try:
            order.delivery_time = datetime.fromisoformat(data['delivery_time'])
        except ValueError:
            return jsonify({'error': 'Invalid delivery_time format'}), 400
    
    try:
        db.session.commit()
        return jsonify({'message': 'Order updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/log_reading', methods=['POST'])
@jwt_required()
def log_reading():
    """
    Log a water meter reading.
    """
    user_id = int(get_jwt_identity())
    
    # FIX 1: Fetch the user object to get their correct Society ID
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.json
    required_fields = ['reading']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    
    try:
        reading_value = float(data['reading'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid reading value'}), 400
    
    timestamp = datetime.utcnow()
    if 'timestamp' in data:
        try:
            timestamp = datetime.fromisoformat(data['timestamp'])
        except ValueError:
            return jsonify({'error': 'Invalid timestamp format'}), 400
    
    # FIX 2: Use user.society_id instead of data.get('society_id')
    reading = WaterReading(
        user_id=user_id,
        reading=reading_value,
        society_id=user.society_id,  # <-- Automatically link to user's society
        timestamp=timestamp
    )

    try:
        db.session.add(reading)
        db.session.commit()
        return jsonify({'message': 'Reading logged'}), 201
    except Exception as e:
        db.session.rollback()
        # This will now print the specific database error if it still fails
        print(f"Database Error: {e}") 
        return jsonify({'error': str(e)}), 500

@api.route('/consumption_report', methods=['GET'])
@jwt_required()
def consumption_report():
    user_id = int(get_jwt_identity())
    period = request.args.get('period', 'daily') # 'daily', 'weekly', 'monthly'

    now = datetime.utcnow()

    if period == 'weekly':
        start_dt = now - timedelta(days=7)
    elif period == 'monthly':
        start_dt = now - timedelta(days=30)
    else: # daily
        start_dt = now - timedelta(days=1)

    readings = WaterReading.query.filter(
        WaterReading.user_id == user_id,
        WaterReading.timestamp >= start_dt
    ).order_by(WaterReading.timestamp).all()

    if not readings:
        return jsonify({
            "period": period,
            "total_usage_liters": 0,
            "daily_breakdown": []
        }), 200

    # Aggregate cumulative meter readings into per-day usage.
    day_bounds = {}
    for r in readings:
        day_key = r.timestamp.date().isoformat()
        if day_key not in day_bounds:
            day_bounds[day_key] = {"first": r.reading, "last": r.reading}
        else:
            day_bounds[day_key]["last"] = r.reading

    daily_breakdown = []
    total_usage = 0.0
    for day in sorted(day_bounds.keys()):
        usage = max(day_bounds[day]["last"] - day_bounds[day]["first"], 0.0)
        usage = round(usage, 2)
        total_usage += usage
        daily_breakdown.append({"date": day, "usage": usage})

    report = {
        "period": period,
        "total_usage_liters": round(total_usage, 2),
        "daily_breakdown": daily_breakdown,
    }

    return jsonify(report), 200


@api.route('/conservation_tips', methods=['GET'])
def conservation_tips():
    """
    Get conservation tips.
    """
    location = request.args.get('location', 'urban_india')
    tips = ConservationTip.query.filter_by(location_specific=location).all()
    return jsonify([{'title': t.title, 'content': t.content} for t in tips]), 200


@api.route('/tankers', methods=['POST'])
@jwt_required()
def create_tanker_listing():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or not _is_owner_role(user.role):
        return jsonify({'error': 'Only tanker owners can create listings'}), 403

    data = request.json or {}
    required_fields = ['vehicle_number', 'capacity', 'price_per_liter']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

    if TankerListing.query.filter_by(vehicle_number=data['vehicle_number']).first():
        return jsonify({'error': 'Vehicle number already exists'}), 400

    try:
        tanker = TankerListing(
            owner_id=user_id,
            vehicle_number=data['vehicle_number'],
            tanker_type=data.get('type', 'Standard'),
            capacity=float(data['capacity']),
            price_per_liter=float(data['price_per_liter']),
            base_delivery_fee=float(data.get('base_delivery_fee', 0.0)),
            service_areas=json.dumps(data.get('service_areas', [])),
            images=json.dumps(data.get('images', [])),
            amenities=json.dumps(data.get('amenities', [])),
            description=data.get('description'),
            emergency_contact=data.get('emergency_contact'),
            status=data.get('status', 'available'),
            area=data.get('area', user.area),
            city=data.get('city', user.city),
            lat=float(data['lat']) if data.get('lat') is not None else user.lat,
            long=float(data['long']) if data.get('long') is not None else user.long,
        )
        db.session.add(tanker)
        db.session.commit()
        return jsonify({'message': 'Tanker listing created', 'tanker': _serialize_tanker(tanker, include_private=True)}), 201
    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({'error': 'Invalid numeric value provided'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/tankers', methods=['GET'])
@jwt_required()
def get_tanker_listings():
    tankers = TankerListing.query.all()
    return jsonify([_serialize_tanker(t) for t in tankers]), 200


@api.route('/tankers/owner', methods=['GET'])
@jwt_required()
def get_owner_tankers():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or not _is_owner_role(user.role):
        return jsonify({'error': 'Only tanker owners can access this resource'}), 403

    tankers = TankerListing.query.filter_by(owner_id=user_id).order_by(TankerListing.created_at.desc()).all()
    return jsonify([_serialize_tanker(t, include_private=True) for t in tankers]), 200


@api.route('/tankers/<int:tanker_id>', methods=['PUT'])
@jwt_required()
def update_tanker_listing(tanker_id):
    user_id = int(get_jwt_identity())
    tanker = TankerListing.query.get(tanker_id)

    if not tanker:
        return jsonify({'error': 'Tanker not found'}), 404
    if tanker.owner_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json or {}
    try:
        if 'vehicle_number' in data:
            existing = TankerListing.query.filter_by(vehicle_number=data['vehicle_number']).first()
            if existing and existing.id != tanker_id:
                return jsonify({'error': 'Vehicle number already exists'}), 400
            tanker.vehicle_number = data['vehicle_number']
        if 'capacity' in data:
            tanker.capacity = float(data['capacity'])
        if 'price_per_liter' in data:
            tanker.price_per_liter = float(data['price_per_liter'])
        if 'base_delivery_fee' in data:
            tanker.base_delivery_fee = float(data['base_delivery_fee'])
        if 'type' in data:
            tanker.tanker_type = data['type']
        if 'service_areas' in data:
            tanker.service_areas = json.dumps(data['service_areas'])
        if 'images' in data:
            tanker.images = json.dumps(data['images'])
        if 'amenities' in data:
            tanker.amenities = json.dumps(data['amenities'])
        if 'description' in data:
            tanker.description = data['description']
        if 'emergency_contact' in data:
            tanker.emergency_contact = data['emergency_contact']
        if 'status' in data:
            tanker.status = data['status']
        if 'area' in data:
            tanker.area = data['area']
        if 'city' in data:
            tanker.city = data['city']
        if 'lat' in data:
            tanker.lat = float(data['lat']) if data['lat'] is not None else None
        if 'long' in data:
            tanker.long = float(data['long']) if data['long'] is not None else None

        db.session.commit()
        return jsonify({'message': 'Tanker updated', 'tanker': _serialize_tanker(tanker, include_private=True)}), 200
    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({'error': 'Invalid numeric value provided'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/tankers/<int:tanker_id>', methods=['DELETE'])
@jwt_required()
def delete_tanker_listing(tanker_id):
    user_id = int(get_jwt_identity())
    tanker = TankerListing.query.get(tanker_id)

    if not tanker:
        return jsonify({'error': 'Tanker not found'}), 404
    if tanker.owner_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        db.session.delete(tanker)
        db.session.commit()
        return jsonify({'message': 'Tanker deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/tankers/<int:tanker_id>/status', methods=['PATCH'])
@jwt_required()
def update_tanker_status(tanker_id):
    user_id = int(get_jwt_identity())
    tanker = TankerListing.query.get(tanker_id)

    if not tanker:
        return jsonify({'error': 'Tanker not found'}), 404
    if tanker.owner_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json or {}
    status = data.get('status')
    if status not in ['available', 'booked', 'maintenance']:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        tanker.status = status
        db.session.commit()
        return jsonify({'message': 'Status updated', 'tanker': _serialize_tanker(tanker, include_private=True)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    user_id = int(get_jwt_identity())
    data = request.json or {}
    required_fields = ['tanker_id', 'quantity', 'total_amount']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

    tanker = TankerListing.query.get(int(data['tanker_id']))
    if not tanker:
        return jsonify({'error': 'Tanker not found'}), 404
    if tanker.status != 'available':
        return jsonify({'error': 'Tanker is not available'}), 400

    try:
        booking = TankerBooking(
            tanker_id=tanker.id,
            customer_id=user_id,
            delivery_address=data.get('delivery_address', 'Address to be shared on confirmation'),
            delivery_pincode=data.get('delivery_pincode'),
            quantity=float(data['quantity']),
            total_amount=float(data['total_amount']),
            status='pending',
            scheduled_time=datetime.fromisoformat(data['scheduled_time']) if data.get('scheduled_time') else None,
        )
        tanker.status = 'booked'
        db.session.add(booking)
        db.session.commit()
        return jsonify({'message': 'Booking created', 'booking_id': booking.id}), 201
    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({'error': 'Invalid numeric or datetime value'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/bookings/owner', methods=['GET'])
@jwt_required()
def get_owner_bookings():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or not _is_owner_role(user.role):
        return jsonify({'error': 'Only tanker owners can access this resource'}), 403

    bookings = TankerBooking.query.join(TankerListing, TankerBooking.tanker_id == TankerListing.id)\
        .filter(TankerListing.owner_id == user_id)\
        .order_by(TankerBooking.created_at.desc()).all()

    result = []
    for b in bookings:
        customer = User.query.get(b.customer_id)
        tanker = TankerListing.query.get(b.tanker_id)
        result.append({
            'id': b.id,
            'tanker_id': b.tanker_id,
            'tanker_vehicle_number': tanker.vehicle_number if tanker else None,
            'customer': {
                'id': customer.id if customer else None,
                'username': customer.username if customer else 'Unknown',
                'email': customer.email if customer else None,
            },
            'delivery_address': b.delivery_address,
            'delivery_pincode': b.delivery_pincode,
            'quantity': b.quantity,
            'total_amount': b.total_amount,
            'status': b.status,
            'scheduled_time': b.scheduled_time.isoformat() if b.scheduled_time else None,
            'delivered_time': b.delivered_time.isoformat() if b.delivered_time else None,
            'created_at': b.created_at.isoformat() if b.created_at else None,
        })
    return jsonify(result), 200


@api.route('/bookings/<int:booking_id>/status', methods=['PATCH'])
@jwt_required()
def update_booking_status(booking_id):
    user_id = int(get_jwt_identity())
    booking = TankerBooking.query.get(booking_id)

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    tanker = TankerListing.query.get(booking.tanker_id)
    if not tanker or tanker.owner_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json or {}
    status = data.get('status')
    if status not in ['pending', 'confirmed', 'in_transit', 'completed', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        booking.status = status
        if status in ['cancelled', 'completed'] and tanker.status == 'booked':
            tanker.status = 'available'
        if status == 'completed':
            booking.delivered_time = datetime.utcnow()
            tanker.total_deliveries = (tanker.total_deliveries or 0) + 1
        db.session.commit()
        return jsonify({'message': 'Booking status updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/owner/dashboard', methods=['GET'])
@jwt_required()
def owner_dashboard():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not _is_owner_role(user.role):
        return jsonify({'error': 'Only tanker owners can access this resource'}), 403

    tankers = TankerListing.query.filter_by(owner_id=user_id).all()
    tanker_ids = [t.id for t in tankers]
    bookings = TankerBooking.query.filter(TankerBooking.tanker_id.in_(tanker_ids)).all() if tanker_ids else []

    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    active_bookings = sum(1 for b in bookings if b.status in ['pending', 'confirmed', 'in_transit'])
    avg_rating = round(sum((t.rating or 0) for t in tankers) / len(tankers), 2) if tankers else 0.0
    month_earnings = sum(
        b.total_amount for b in bookings
        if b.status == 'completed' and b.delivered_time and b.delivered_time >= month_start
    )
    pending_bookings = sum(1 for b in bookings if b.status == 'pending')

    recent = sorted(bookings, key=lambda b: b.created_at or datetime.min, reverse=True)[:6]
    activity = [{
        'booking_id': b.id,
        'tanker_id': b.tanker_id,
        'status': b.status,
        'total_amount': b.total_amount,
        'quantity': b.quantity,
        'created_at': b.created_at.isoformat() if b.created_at else None,
    } for b in recent]

    return jsonify({
        'total_tankers': len(tankers),
        'active_bookings': active_bookings,
        'this_month_earnings': round(month_earnings, 2),
        'average_rating': avg_rating,
        'pending_bookings': pending_bookings,
        'recent_activity': activity,
    }), 200


@api.route('/owner/earnings', methods=['GET'])
@jwt_required()
def owner_earnings():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not _is_owner_role(user.role):
        return jsonify({'error': 'Only tanker owners can access this resource'}), 403

    tankers = TankerListing.query.filter_by(owner_id=user_id).all()
    tanker_ids = [t.id for t in tankers]
    if not tanker_ids:
        return jsonify({'total_earnings': 0, 'completed_orders': 0, 'monthly': [], 'by_tanker': []}), 200

    completed = TankerBooking.query.filter(
        TankerBooking.tanker_id.in_(tanker_ids),
        TankerBooking.status == 'completed'
    ).all()

    total_earnings = round(sum(b.total_amount for b in completed), 2)
    completed_orders = len(completed)

    monthly = defaultdict(float)
    for b in completed:
        dt = b.delivered_time or b.created_at
        key = dt.strftime('%Y-%m') if dt else 'unknown'
        monthly[key] += b.total_amount

    by_tanker = defaultdict(float)
    for b in completed:
        by_tanker[b.tanker_id] += b.total_amount

    tanker_map = {t.id: t for t in tankers}

    return jsonify({
        'total_earnings': total_earnings,
        'completed_orders': completed_orders,
        'monthly': [
            {'month': month, 'amount': round(amount, 2)}
            for month, amount in sorted(monthly.items())
        ],
        'by_tanker': [
            {
                'tanker_id': tanker_id,
                'vehicle_number': tanker_map[tanker_id].vehicle_number if tanker_id in tanker_map else 'Unknown',
                'amount': round(amount, 2)
            }
            for tanker_id, amount in by_tanker.items()
        ]
    }), 200

@api.route('/challenges', methods=['GET'])
@jwt_required()
def challenges():
    """
    Get list of available challenges.
    """
    chals = Challenge.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'short_desc': c.short_desc,
        'full_desc': c.full_desc,
        'water_save_potential': c.water_save_potential,
        'eco_points': c.eco_points
    } for c in chals]), 200

@api.route('/start_challenge/<int:challenge_id>', methods=['POST'])
@jwt_required()
def start_challenge(challenge_id):
    """
    Start a new challenge for the user.
    """
    user_id = int(get_jwt_identity())
    chal = Challenge.query.get(challenge_id)
    if not chal:
        return jsonify({'error': 'Challenge not found'}), 404
    existing = UserChallenge.query.filter_by(user_id=user_id, challenge_id=challenge_id).first()
    if existing:
        return jsonify({'error': 'Challenge already started'}), 400
    uc = UserChallenge(
        user_id=user_id,
        challenge_id=challenge_id,
        status='active',
        start_date=datetime.utcnow()
    )
    try:
        db.session.add(uc)
        db.session.commit()
        return jsonify({'message': 'Challenge started', 'user_challenge_id': uc.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/user_challenges', methods=['GET'])
@jwt_required()
def user_challenges():
    """
    Get user's challenges with progress.
    """
    user_id = int(get_jwt_identity())
    ucs = UserChallenge.query.filter_by(user_id=user_id).all()
    result = []
    for uc in ucs:
        chal = Challenge.query.get(uc.challenge_id)
        result.append({
            'id': uc.id,
            'challenge_id': uc.challenge_id,
            'name': chal.name,
            'short_desc': chal.short_desc,
            'full_desc': chal.full_desc,
            'progress': uc.progress,
            'status': uc.status,
            'start_date': uc.start_date.isoformat() if uc.start_date else None,
            'end_date': uc.end_date.isoformat() if uc.end_date else None,
            'water_saved': uc.water_saved,
            'eco_points_earned': uc.eco_points_earned
        })
    return jsonify(result), 200

@api.route('/update_challenge_progress/<int:user_challenge_id>', methods=['PUT'])
@jwt_required()
def update_challenge_progress(user_challenge_id):
    """
    Update progress for a user challenge.
    """
    user_id = int(get_jwt_identity())
    data = request.json
    if 'progress' not in data:
        return jsonify({'error': 'Missing progress'}), 400
    try:
        progress = float(data['progress'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid progress value'}), 400
    uc = UserChallenge.query.get(user_challenge_id)
    if not uc or uc.user_id != user_id:
        return jsonify({'error': 'Unauthorized or not found'}), 403
    uc.progress = progress
    if uc.progress >= 100:
        chal = Challenge.query.get(uc.challenge_id)
        uc.status = 'completed'
        uc.end_date = datetime.utcnow()
        uc.water_saved = chal.water_save_potential
        uc.eco_points_earned = chal.eco_points
    try:
        db.session.commit()
        return jsonify({'message': 'Progress updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/conservation_summary', methods=['GET'])
@jwt_required()
def conservation_summary():
    """
    Get conservation hub summary.
    """
    user_id = int(get_jwt_identity())
    now = datetime.utcnow()
    this_month_start = datetime(now.year, now.month, 1)
    water_saved_month = db.session.query(db.func.sum(UserChallenge.water_saved)).filter(
        UserChallenge.user_id == user_id,
        UserChallenge.end_date >= this_month_start
    ).scalar() or 0.0
    active_count = UserChallenge.query.filter_by(user_id=user_id, status='active').count()
    eco_points = db.session.query(db.func.sum(UserChallenge.eco_points_earned)).filter_by(
        user_id=user_id
    ).scalar() or 0
    return jsonify({
        'water_saved_this_month': water_saved_month,
        'active_challenges': active_count,
        'eco_points_earned': eco_points
    }), 200

@api.route('/society_bulk_order', methods=['POST'])
@jwt_required()
def society_bulk_order():
    """
    Place bulk tanker order (society admin only).
    """
    claims = get_jwt()
    if claims.get('role') != 'society_admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    required_fields = ['supplier_id', 'volume', 'price', 'society_id']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    
    try:
        supplier_id = int(data['supplier_id'])
        volume = float(data['volume'])
        price = float(data['price'])
        society_id = int(data['society_id'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid data types'}), 400
    
    supplier = Supplier.query.get(supplier_id)
    society = Society.query.get(society_id)
    if not supplier:
        return jsonify({'error': 'Supplier not found'}), 404
    if not society:
        return jsonify({'error': 'Society not found'}), 404
    
    order = TankerOrder(
        supplier_id=supplier_id,
        volume=volume,
        price=price,
        status='pending',
        society_id=society_id
    )
    try:
        db.session.add(order)
        db.session.commit()
        return jsonify({'message': 'Bulk order placed', 'order_id': order.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/society_dashboard', methods=['GET'])
@jwt_required()
def society_dashboard():
    """
    Get society management dashboard data using dynamically 
    aggregated daily data from Spark.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if user.society_id is None:
        return jsonify({'message': 'No society associated'}), 200
    
    society_id = user.society_id
    current_year = datetime.utcnow().year
    y_start = datetime(current_year, 1, 1)

    # --- 1. Monthly Consumption (Aggregating Spark's Daily Output) ---
    # We extract the month from the 'date' column and SUM the daily usage
    monthly_data = db.session.query(
        extract('month', UserDailyUsage.date).label('month'),
        func.sum(UserDailyUsage.total_usage_liters).label('total_consumption')
    ).filter(
        UserDailyUsage.society_id == society_id,
        extract('year', UserDailyUsage.date) == current_year
    ).group_by(
        extract('month', UserDailyUsage.date)
    ).all()

    # Convert to dictionary { month_int: total_float }
    monthly_consumption = {int(row.month): row.total_consumption for row in monthly_data}

    # Fill missing months with 0
    for m in range(1, 13):
        if m not in monthly_consumption:
            monthly_consumption[m] = 0.0

    # --- 2. Lightweight Queries (Standard SQL) ---
    
    # Tankers Ordered YTD
    orders = TankerOrder.query.filter(
        TankerOrder.society_id == society_id,
        TankerOrder.order_time >= y_start
    ).all()
    tankers_ytd = len(orders)
    total_volume_ytd = sum(o.volume for o in orders)

    # Active Initiatives & Water Saved
    society_users = User.query.filter_by(society_id=society_id).with_entities(User.id).all()
    user_ids = [u.id for u in society_users]

    water_saved = 0.0
    active_initiatives = 0
    percs = {'active': 0, 'pending': 0, 'completed': 0}

    if user_ids:
        water_saved = db.session.query(func.sum(UserChallenge.water_saved))\
            .filter(UserChallenge.user_id.in_(user_ids)).scalar() or 0.0
            
        active_initiatives = db.session.query(func.count(distinct(UserChallenge.challenge_id)))\
            .filter(UserChallenge.user_id.in_(user_ids), UserChallenge.status == 'active').scalar()

        # Impact Percentages
        total_ucs = UserChallenge.query.filter(UserChallenge.user_id.in_(user_ids)).count()
        if total_ucs > 0:
            counts = db.session.query(
                UserChallenge.status, func.count(UserChallenge.status)
            ).filter(UserChallenge.user_id.in_(user_ids)).group_by(UserChallenge.status).all()
            
            counts_dict = {status: count for status, count in counts}
            
            percs['active'] = (counts_dict.get('active', 0) / total_ucs) * 100
            percs['pending'] = (counts_dict.get('pending', 0) / total_ucs) * 100
            percs['completed'] = (counts_dict.get('completed', 0) / total_ucs) * 100

    # Scheduled Deliveries
    pending_orders = TankerOrder.query.filter(
        TankerOrder.society_id == society_id,
        TankerOrder.status.in_(['pending', 'en_route'])
    ).all()
    
    deliveries = []
    for o in pending_orders:
        sup = Supplier.query.get(o.supplier_id)
        deliveries.append({
            'supplier': sup.name if sup else 'Unknown',
            'date': o.delivery_time.date().isoformat() if o.delivery_time else None,
            'time': o.delivery_time.time().isoformat() if o.delivery_time else None,
            'volume': o.volume,
            'status': o.status
        })

    return jsonify({
        'monthly_consumption': monthly_consumption,
        'tankers_ordered_ytd': tankers_ytd,
        'total_volume_ytd': total_volume_ytd,
        'active_initiatives': active_initiatives,
        'water_saved': water_saved,
        'conservation_impact': percs,
        'scheduled_deliveries': deliveries
    }), 200
    

@api.route('/community/broadcasts', methods=['GET', 'POST'])
@jwt_required()
def handle_broadcasts():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.society_id:
        return jsonify({'error': 'User not in a society'}), 403

    # GET: Fetch all broadcasts for the user's society
    if request.method == 'GET':
        broadcasts = Broadcast.query.filter_by(society_id=user.society_id)\
            .order_by(Broadcast.created_at.desc()).all()
        return jsonify([{
            'id': b.id,
            'title': b.title,
            'content': b.content,
            'created_at': b.created_at.isoformat()
        } for b in broadcasts]), 200

    # POST: Create a new broadcast (Admin Only)
    if request.method == 'POST':
        if user.role != 'society_admin':
            return jsonify({'error': 'Only admins can post broadcasts'}), 403
        
        data = request.json
        if not data.get('title') or not data.get('content'):
            return jsonify({'error': 'Missing title or content'}), 400
            
        new_broadcast = Broadcast(
            society_id=user.society_id,
            title=data['title'],
            content=data['content']
        )
        db.session.add(new_broadcast)
        db.session.commit()
        return jsonify({'message': 'Broadcast posted successfully'}), 201

@api.route('/community/threads', methods=['GET', 'POST'])
@jwt_required()
def handle_threads():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.society_id:
        return jsonify({'error': 'User not in a society'}), 403

    # GET: List all discussion threads
    if request.method == 'GET':
        threads = DiscussionThread.query.filter_by(society_id=user.society_id)\
            .order_by(DiscussionThread.created_at.desc()).all()
        return jsonify([{
            'id': t.id,
            'title': t.title,
            'content': t.content,
            'category': t.category,
            'author': t.author.username,
            'created_at': t.created_at.isoformat(),
            'comment_count': t.comments.count()
        } for t in threads]), 200

    # POST: Create a new thread
    if request.method == 'POST':
        data = request.json
        if not data.get('title') or not data.get('content'):
            return jsonify({'error': 'Missing title or content'}), 400
            
        new_thread = DiscussionThread(
            society_id=user.society_id,
            user_id=user_id,
            title=data['title'],
            content=data['content'],
            category=data.get('category', 'General')
        )
        db.session.add(new_thread)
        db.session.commit()
        return jsonify({'message': 'Thread created', 'id': new_thread.id}), 201

@api.route('/community/threads/<int:thread_id>/comments', methods=['GET', 'POST'])
@jwt_required()
def handle_comments(thread_id):
    user_id = int(get_jwt_identity())
    
    # GET: Fetch comments for a specific thread
    if request.method == 'GET':
        comments = ThreadComment.query.filter_by(thread_id=thread_id)\
            .order_by(ThreadComment.created_at.asc()).all()
        return jsonify([{
            'id': c.id,
            'content': c.content,
            'author': c.author.username,
            'created_at': c.created_at.isoformat()
        } for c in comments]), 200

    # POST: Add a comment
    if request.method == 'POST':
        data = request.json
        if not data.get('content'):
            return jsonify({'error': 'Missing content'}), 400
            
        new_comment = ThreadComment(
            thread_id=thread_id,
            user_id=user_id,
            content=data['content']
        )
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({'message': 'Comment added'}), 201
    
@api.route("/create-payment-intent", methods=["POST"])
@jwt_required()
def create_payment_intent():
    """
    Create a Stripe payment intent for water tanker booking.
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.json
        
        # Validate required fields
        if not data.get("amount") or not data.get("booking_id"):
            return jsonify({"error": "Missing required fields: amount and booking_id"}), 400
        
        amount = float(data["amount"])  # amount in rupees
        booking_id = data["booking_id"]
        
        # Validate amount
<<<<<<< HEAD
        if amount <= 0:
=======
        # We set a minimum amount of 40 rupees to avoid microtransactions that Stripe might block
        if amount <= 40:
>>>>>>> ef41028992d414d624bbd2afc66f4481efb5c6af
            return jsonify({"error": "Invalid amount"}), 400
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # convert to paise
            currency="inr",
            payment_method_types=["card"],
            metadata={
                "booking_id": booking_id,
                "user_id": user_id
            }
        )
        
        return jsonify({
            "clientSecret": intent.client_secret
        }), 200
        
    except ValueError as e:
        return jsonify({"error": "Invalid amount format"}), 400
    except Exception as e:
        print(f"Stripe payment intent error: {e}")
        return jsonify({"error": "Failed to create payment intent"}), 500
