# auth.py
from flask_jwt_extended import create_access_token
from models import User, db


def normalize_role(role: str) -> str:
    role_map = {
        'customer': 'user',
        'user': 'user',
        'tanker_owner': 'tanker_owner',
        'supplier': 'supplier',
        'admin': 'society_admin',
        'society_admin': 'society_admin',
    }
    return role_map.get((role or '').strip().lower(), 'user')

def register_user(username, email, password, role='user', society_id=None, area=None, city=None, lat=None, long=None):
    """
    Register a new user with validation.
    """
    if not all([username, email, password]):
        return None, 'Missing required fields'
    normalized_role = normalize_role(role)
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return None, 'User already exists'
    user = User(username=username, email=email, role=normalized_role, society_id=society_id, area=area, city=city, lat=lat, long=long)
    user.set_password(password)
    try:
        db.session.add(user)
        db.session.commit()
        return user, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def login_user(identifier, password):
    """
    Login user and generate JWT token.
    """
    if not all([identifier, password]):
        return None, 'Missing credentials'
    user = User.query.filter_by(username=identifier).first() or User.query.filter_by(email=identifier).first()
    if user and user.check_password(password):
        # Use user.id as a string for the identity, add role as a custom claim
        access_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
        return access_token, None
    return None, 'Invalid credentials'