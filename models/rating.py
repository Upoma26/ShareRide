from datetime import datetime

from extensions import db


class Rating(db.Model):
    _tablename_ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ratee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    stars = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship("Booking", backref="ratings")
    rater = db.relationship("User", foreign_keys=[rater_id])
    ratee = db.relationship("User", foreign_keys=[ratee_id])

    _table_args_ = (
        db.UniqueConstraint("booking_id", "rater_id", name="uq_one_rating_per_booking"),
        db.CheckConstraint("stars >= 1 AND stars <= 5", name="ck_stars_range"),
    )