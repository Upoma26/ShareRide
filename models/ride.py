from datetime import datetime

from extensions import db

RIDE_STATUSES = ("scheduled", "started", "completed", "cancelled")


class Ride(db.Model):
    __tablename__ = "rides"

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)

    pickup = db.Column(db.String(150), nullable=False)
    destination = db.Column(db.String(150), nullable=False)
    ride_date = db.Column(db.Date, nullable=False)
    ride_time = db.Column(db.Time, nullable=False)

    total_seats = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    fare_per_seat = db.Column(db.Integer, nullable=False)

    notes = db.Column(db.String(300))
    status = db.Column(db.String(20), nullable=False, default="scheduled")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    provider = db.relationship("User", backref="rides_offered")
    vehicle = db.relationship("Vehicle", backref="rides")

    __table_args__ = (
        db.CheckConstraint("available_seats >= 0", name="ck_seats_not_negative"),
        db.CheckConstraint("available_seats <= total_seats", name="ck_seats_within_total"),
        db.CheckConstraint("fare_per_seat >= 0", name="ck_fare_not_negative"),
    )

    @property
    def is_full(self):
        return self.available_seats == 0

    @property
    def booked_seats(self):
        return self.total_seats - self.available_seats

    def __repr__(self):
        return f"<Ride {self.pickup} -> {self.destination} on {self.ride_date}>"