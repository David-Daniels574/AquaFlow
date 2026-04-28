from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class WaterReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # auth_service user id
    society_id = db.Column(db.Integer, nullable=True)  # auth_service society id
    reading = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class UserMeterState(db.Model):
    __tablename__ = "user_meter_state"
    user_id = db.Column(db.Integer, primary_key=True)  # auth_service user id
    last_reading = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.Date, nullable=False)


class UserDailyUsage(db.Model):
    __tablename__ = "user_daily_usage"
    user_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    society_id = db.Column(db.Integer)
    total_usage_liters = db.Column(db.Float)
    __table_args__ = (db.UniqueConstraint("user_id", "date", name="uq_user_date"),)
