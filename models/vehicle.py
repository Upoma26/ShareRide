from datetime import datetime

from extensions import db

VEHICLE_TYPES = ("car", "microbus", "bike", "cng")


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    vehicle_type = db.Column(db.String(20), nullable=False, default="car")
    brand = db.Column(db.String(60), nullable=False)
    model = db.Column(db.String(60), nullable=False)
    color = db.Column(db.String(30))
    plate_number = db.Column(db.String(30), unique=True, nullable=False)
    seat_capacity = db.Column(db.Integer, nullable=False)

    registration_doc = db.Column(db.String(255))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("User", backref="vehicles")

    def __repr__(self):
        return f"<Vehicle {self.plate_number} ({self.vehicle_type})>"