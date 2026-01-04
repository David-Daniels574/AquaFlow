from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, User, Supplier, TankerOrder, WaterReading, ConservationTip, Society, SupplierOffer, Challenge, UserChallenge, Broadcast, DiscussionThread, ThreadComment, SocietyMonthlySummary
from auth import register_user, login_user
from utils import get_consumption_reports, calculate_eta, get_road_metrics
from datetime import datetime, timedelta
from collections import defaultdict
import stripe 
from dotenv import load_dotenv
import os
from sqlalchemy import func, distinct
from app import cache,db

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

api = Blueprint('api', __name__)

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
    """
    Get consumption report.
    """
    user_id = int(get_jwt_identity())
    period = request.args.get('period', 'daily')
    detailed = request.args.get('detailed', False, type=bool)
    report = get_consumption_reports(user_id, period)
    if 'error' in report:
        return jsonify({'error': report['error']}), 400
    if detailed:
        now = datetime.utcnow()
        if period == 'daily':
            start = now - timedelta(days=1)
        elif period == 'weekly':
            start = now - timedelta(weeks=1)
        elif period == 'monthly':
            start = now - timedelta(days=30)
        else:
            start = now - timedelta(days=30)
        readings = WaterReading.query.filter(
            WaterReading.user_id == user_id,
            WaterReading.timestamp >= start
        ).order_by(WaterReading.timestamp).all()
        report['readings'] = [{'timestamp': r.timestamp.isoformat(), 'reading': r.reading} for r in readings]
    return jsonify(report), 200


@api.route('/conservation_tips', methods=['GET'])
def conservation_tips():
    """
    Get conservation tips.
    """
    location = request.args.get('location', 'urban_india')
    tips = ConservationTip.query.filter_by(location_specific=location).all()
    return jsonify([{'title': t.title, 'content': t.content} for t in tips]), 200

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
    Get society management dashboard data using Spark Aggregates.
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

    # --- 1. Monthly Consumption (POWERED BY SPARK) ---
    # Query the summary table directly. 
    # No more looping through millions of WaterReading rows!
    spark_summaries = SocietyMonthlySummary.query.filter_by(
        society_id=society_id,
        year=current_year
    ).all()

    # Convert to dictionary { month_int: total_float }
    monthly_consumption = {row.month: row.total_consumption for row in spark_summaries}

    # Fill missing months with 0
    for m in range(1, 13):
        if m not in monthly_consumption:
            monthly_consumption[m] = 0.0

    # --- 2. Lightweight Queries (Can stay as standard SQL) ---
    
    # Tankers Ordered YTD
    orders = TankerOrder.query.filter(
        TankerOrder.society_id == society_id,
        TankerOrder.order_time >= y_start
    ).all()
    tankers_ytd = len(orders)
    total_volume_ytd = sum(o.volume for o in orders)

    # Active Initiatives & Water Saved
    # These tables are usually small, so standard SQL is fine.
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
            
            # Convert list of tuples [('active', 5), ('pending', 2)] to dict
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
        if amount <= 0:
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
