from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, User, Supplier, TankerOrder, WaterReading, ConservationTip, Society, SupplierOffer, Challenge, UserChallenge, LeakEvent
from auth import register_user, login_user
from utils import detect_leak, get_consumption_reports, haversine, calculate_eta, get_severity
from datetime import datetime, timedelta
from collections import defaultdict

api = Blueprint('api', __name__)

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
    Get or update user profile.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if request.method == 'GET':
        return jsonify({
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'society_id': user.society_id,
            'area': user.area,
            'city': user.city,
            'lat': user.lat,
            'long': user.long
        }), 200

    data = request.json
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
    if updated:
        try:
            db.session.commit()
            return jsonify({'message': 'Profile updated'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    return jsonify({'message': 'No updates provided'}), 200

@api.route('/suppliers', methods=['GET'])
@jwt_required()
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
            distance = haversine(user.lat, user.long, s.lat, s.long)
            eta = calculate_eta(distance)  # in minutes
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
            'estimated_eta': eta
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
    
    reading = WaterReading(
        user_id=user_id,
        reading=reading_value,
        society_id=data.get('society_id'),
        timestamp=timestamp
    )
    try:
        db.session.add(reading)
        db.session.commit()
        return jsonify({'message': 'Reading logged'}), 201
    except Exception as e:
        db.session.rollback()
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

@api.route('/leak_detection', methods=['GET'])
@jwt_required()
def leak_detection():
    """
    Check for potential leaks and get history.
    """
    user_id = int(get_jwt_identity())
    threshold = request.args.get('threshold', 5.0, type=float)
    has_leak, message, loss = detect_leak(user_id, threshold)
    severity = None
    desc = None
    if has_leak:
        severity, desc = get_severity(loss)
        now = datetime.utcnow()
        today = now.date()
        existing = LeakEvent.query.filter(
            LeakEvent.user_id == user_id,
            db.func.date(LeakEvent.detected_date) == today
        ).first()
        if not existing:
            leak = LeakEvent(
                user_id=user_id,
                detected_date=now,
                estimated_loss=loss,
                severity=severity,
                description=desc
            )
            db.session.add(leak)
            db.session.commit()
    history = LeakEvent.query.filter_by(user_id=user_id).order_by(LeakEvent.detected_date.desc()).all()
    hist_list = [{
        'date': h.detected_date.isoformat(),
        'loss': h.estimated_loss,
        'severity': h.severity,
        'description': h.description
    } for h in history]
    return jsonify({
        'has_leak': has_leak,
        'estimated_loss': loss,
        'severity': severity,
        'message': message,
        'description': desc,
        'history': hist_list
    }), 200

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
    Get society management dashboard data (accessible by users with society_id).
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Check if user exists
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    # Check if user has a society association
    if user.society_id is None:
        # Return empty dashboard data instead of error
        return jsonify({
            'monthly_consumption': {},
            'total_consumption': 0,
            'average_daily': 0,
            'message': 'No society associated with this user. Please contact an administrator.'
        }), 200
    
    # Get society_id for further processing
    society_id = user.society_id
    
    now = datetime.utcnow()
    current_year = now.year
    y_start = datetime(current_year, 1, 1)
    
    # Monthly consumption for the year
    monthly_consumption = {}
    for m in range(1, 13):
        start = datetime(current_year, m, 1)
        next_month = m + 1 if m < 12 else 1
        year_next = current_year if m < 12 else current_year + 1
        end = datetime(year_next, next_month, 1)
        readings = WaterReading.query.filter(
            WaterReading.society_id == society_id,
            WaterReading.timestamp >= start,
            WaterReading.timestamp < end
        ).order_by(WaterReading.timestamp).all()
        if readings:
            user_readings = defaultdict(list)
            for r in readings:
                user_readings[r.user_id].append(r)
            total_cons = 0.0
            for urs in user_readings.values():
                urs.sort(key=lambda x: x.timestamp)
                for i in range(1, len(urs)):
                    total_cons += urs[i].reading - urs[i-1].reading
            monthly_consumption[m] = total_cons
        else:
            monthly_consumption[m] = 0.0
    
    # Tankers ordered YTD
    orders = TankerOrder.query.filter(
        TankerOrder.society_id == society_id,
        TankerOrder.order_time >= y_start
    ).all()
    tankers_ytd = len(orders)
    total_volume_ytd = sum(o.volume for o in orders)
    
    # Get society users
    society_users = User.query.filter_by(society_id=society_id).all()
    user_ids = [u.id for u in society_users]
    
    # Water saved (approx)
    water_saved = db.session.query(db.func.sum(UserChallenge.water_saved)).filter(
        UserChallenge.user_id.in_(user_ids)
    ).scalar() or 0.0
    
    # Active initiatives (distinct challenges active in society)
    active_initiatives = db.session.query(db.func.count(db.distinct(UserChallenge.challenge_id))).filter(
        UserChallenge.user_id.in_(user_ids),
        UserChallenge.status == 'active'
    ).scalar()
    
    # Conservation impact percentages
    total_ucs = UserChallenge.query.filter(UserChallenge.user_id.in_(user_ids)).count()
    percs = {'active': 0, 'pending': 0, 'completed': 0}
    if total_ucs > 0:
        active_count = UserChallenge.query.filter(
            UserChallenge.user_id.in_(user_ids), UserChallenge.status == 'active'
        ).count()
        pending_count = UserChallenge.query.filter(
            UserChallenge.user_id.in_(user_ids), UserChallenge.status == 'pending'
        ).count()
        completed_count = UserChallenge.query.filter(
            UserChallenge.user_id.in_(user_ids), UserChallenge.status == 'completed'
        ).count()
        percs = {
            'active': (active_count / total_ucs) * 100,
            'pending': (pending_count / total_ucs) * 100,
            'completed': (completed_count / total_ucs) * 100
        }
    
    # Scheduled tanker deliveries
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