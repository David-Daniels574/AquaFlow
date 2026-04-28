from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ConservationTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    location_specific = db.Column(db.String(64))


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    short_desc = db.Column(db.String(256), nullable=False)
    full_desc = db.Column(db.Text, nullable=False)
    water_save_potential = db.Column(db.Float, nullable=False)
    eco_points = db.Column(db.Integer, nullable=False)


class UserChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # auth_service user id
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenge.id"), nullable=False)
    progress = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="pending")
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    water_saved = db.Column(db.Float, default=0.0)
    eco_points_earned = db.Column(db.Integer, default=0)

    challenge = db.relationship("Challenge", backref="user_challenges")


class Broadcast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    society_id = db.Column(db.Integer, nullable=False)  # auth_service society id
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DiscussionThread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    society_id = db.Column(db.Integer, nullable=False)  # auth_service society id
    user_id = db.Column(db.Integer, nullable=False)  # auth_service user id
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship("ThreadComment", backref="thread", lazy="dynamic", cascade="all, delete-orphan")


class ThreadComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("discussion_thread.id"), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # auth_service user id
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
