from datetime import datetime

from extensions import db

BOOKING_STATUSES = ("pending", "accepted", "onboard", "rejected", "cancelled", "completed")


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    seats = db.Column(db.Integer, nullable=False, default=1)
    total_fare = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")

    trip_pin_hash = db.Column(db.String(255))
    pin_attempts = db.Column(db.Integer, default=0)
    pin_generated_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    decided_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)

    ride = db.relationship("Ride", backref="bookings")
    seeker = db.relationship("User", backref="bookings")

    __table_args__ = (
        db.CheckConstraint("seats >= 1", name="ck_booking_seats_positive"),
        db.CheckConstraint("total_fare >= 0", name="ck_booking_fare_not_negative"),
    )

    @property
    def is_active(self):
        return self.status in ("pending", "accepted")

    def __repr__(self):
        return f"<Booking {self.id} ride={self.ride_id} seats={self.seats} {self.status}>"