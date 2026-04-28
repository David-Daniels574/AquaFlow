from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class TankerBooking(db.Model):
    __tablename__ = "tanker_booking"

    id = db.Column(db.Integer, primary_key=True)
    tanker_id = db.Column(db.Integer, nullable=False)  # external supplier_service id
    owner_id = db.Column(db.Integer, nullable=False)  # external auth_service user id
    tanker_vehicle_number = db.Column(db.String(32))
    customer_id = db.Column(db.Integer, nullable=False)  # external auth_service user id
    delivery_address = db.Column(db.String(256))
    delivery_pincode = db.Column(db.String(16))
    quantity = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")
    scheduled_time = db.Column(db.DateTime)
    delivered_time = db.Column(db.DateTime)
    customer_rating = db.Column(db.Integer)
    customer_review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TankerOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)  # external auth_service user id
    supplier_id = db.Column(db.Integer, nullable=False)  # external supplier_service id
    society_id = db.Column(db.Integer, nullable=True)  # external auth_service society id
    volume = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")
    order_time = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_time = db.Column(db.DateTime, nullable=True)
    tracking_lat = db.Column(db.Float)
    tracking_long = db.Column(db.Float)
