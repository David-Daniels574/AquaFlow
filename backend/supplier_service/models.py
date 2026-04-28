from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Supplier(db.Model):
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

    offers = db.relationship("SupplierOffer", backref="supplier", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "contact": self.contact,
            "photo_url": self.photo_url,
            "area": self.area,
            "city": self.city,
            "rating": self.rating,
            "num_reviews": self.num_reviews,
            "lat": self.lat,
            "long": self.long,
            "verified": self.verified,
        }


class SupplierOffer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"id": self.id, "supplier_id": self.supplier_id, "quantity": self.quantity, "cost": self.cost}


class TankerListing(db.Model):
    __tablename__ = "tanker_listing"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, nullable=False)  # user id from auth_service
    vehicle_number = db.Column(db.String(32), unique=True, nullable=False)
    tanker_type = db.Column(db.String(50), default="Standard")
    capacity = db.Column(db.Float, nullable=False)
    price_per_liter = db.Column(db.Float, nullable=False)
    base_delivery_fee = db.Column(db.Float, default=0.0)
    service_areas = db.Column(db.Text, default="[]")
    images = db.Column(db.Text, default="[]")
    amenities = db.Column(db.Text, default="[]")
    description = db.Column(db.Text)
    emergency_contact = db.Column(db.String(64))
    status = db.Column(db.String(20), default="available")
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    total_deliveries = db.Column(db.Integer, default=0)
    area = db.Column(db.String(128))
    city = db.Column(db.String(128))
    lat = db.Column(db.Float)
    long = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
