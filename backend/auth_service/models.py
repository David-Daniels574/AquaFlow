from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Society(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(256), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "address": self.address}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    society_id = db.Column(db.Integer, db.ForeignKey("society.id"), nullable=True)
    area = db.Column(db.String(128))
    city = db.Column(db.String(128))
    lat = db.Column(db.Float)
    long = db.Column(db.Float)

    society = db.relationship("Society", backref="users", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "society_id": self.society_id,
            "area": self.area,
            "city": self.city,
            "lat": self.lat,
            "long": self.long,
        }
