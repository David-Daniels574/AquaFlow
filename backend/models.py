# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache

db = SQLAlchemy()
cache = Cache()

class User(db.Model):
    """
    User model for authentication and roles.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'supplier', 'society_admin'
    society_id = db.Column(db.Integer, db.ForeignKey('society.id'))
    area = db.Column(db.String(128))
    city = db.Column(db.String(128))
    lat = db.Column(db.Float)
    long = db.Column(db.Float)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Society(db.Model):
    """
    Society model for residential groups.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    users = db.relationship('User', backref='society', lazy='dynamic')

    def __repr__(self):
        return f'<Society {self.name}>'

class Supplier(db.Model):
    """
    Supplier model for water tanker providers.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    contact = db.Column(db.String(64), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    photo_url = db.Column(db.String(256))
    area = db.Column(db.String(128))
    city = db.Column(db.String(128))
    rating = db.Column(db.Float, default=0.0)
    num_reviews = db.Column(db.Integer, default=0)
    lat = db.Column(db.Float)
    long = db.Column(db.Float)
    offers = db.relationship('SupplierOffer', backref='supplier', lazy='dynamic')

    def __repr__(self):
        return f'<Supplier {self.name}>'

class SupplierOffer(db.Model):
    """
    Model for supplier water quantities and costs.
    """
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<SupplierOffer {self.id}>'

class TankerOrder(db.Model):
    """
    TankerOrder model for booking water deliveries.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    society_id = db.Column(db.Integer, db.ForeignKey('society.id'))
    volume = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'en_route', 'delivered'
    order_time = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_time = db.Column(db.DateTime)
    tracking_lat = db.Column(db.Float)
    tracking_long = db.Column(db.Float)

    def __repr__(self):
        return f'<TankerOrder {self.id}>'

class WaterReading(db.Model):
    """
    WaterReading model for logging consumption.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    society_id = db.Column(db.Integer, db.ForeignKey('society.id'))
    reading = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WaterReading {self.id}>'

class ConservationTip(db.Model):
    """
    ConservationTip model for water saving advice.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    location_specific = db.Column(db.String(64))  # e.g., 'urban_india'

    def __repr__(self):
        return f'<ConservationTip {self.title}>'

class Challenge(db.Model):
    """
    Challenge model for water conservation challenges.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    short_desc = db.Column(db.String(256), nullable=False)
    full_desc = db.Column(db.Text, nullable=False)
    water_save_potential = db.Column(db.Float, nullable=False)
    eco_points = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Challenge {self.name}>'

class UserChallenge(db.Model):
    """
    UserChallenge model for tracking user progress in challenges.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    progress = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'active', 'completed'
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    water_saved = db.Column(db.Float, default=0.0)
    eco_points_earned = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<UserChallenge {self.id}>'

class Broadcast(db.Model):
    """
    Official announcements from Society Admins.
    """
    id = db.Column(db.Integer, primary_key=True)
    society_id = db.Column(db.Integer, db.ForeignKey('society.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Only admins can create these, but we don't need a specific user_id link 
    # if we just want to know it came from the 'Society Office'

    def __repr__(self):
        return f'<Broadcast {self.title}>'

class DiscussionThread(db.Model):
    """
    Community discussion threads started by residents.
    """
    id = db.Column(db.Integer, primary_key=True)
    society_id = db.Column(db.Integer, db.ForeignKey('society.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General') # e.g., 'General', 'Issue', 'Suggestion'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='threads')
    comments = db.relationship('ThreadComment', backref='thread', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Thread {self.title}>'

class ThreadComment(db.Model):
    """
    Replies to discussion threads.
    """
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('discussion_thread.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref='comments')

    def __repr__(self):
        return f'<Comment {self.id}>'
    
# Add this to backend/models.py
class SocietyMonthlySummary(db.Model):
    __tablename__ = 'society_monthly_summary'
    # Composite PK for SQLAlchemy mapping
    society_id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, primary_key=True)
    total_consumption = db.Column(db.Float)