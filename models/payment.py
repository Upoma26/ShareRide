from datetime import datetime

from extensions import db

PAYMENT_METHODS = ("cash", "bkash", "nagad", "card")
PAYMENT_STATUSES = ("pending", "paid", "refunded", "failed")


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), unique=True, nullable=False)

    amount = db.Column(db.Integer, nullable=False)
    method = db.Column(db.String(20), nullable=False, default="cash")
    status = db.Column(db.String(20), nullable=False, default="pending")

    transaction_ref = db.Column(db.String(60))
    receipt_number = db.Column(db.String(30), unique=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

    booking = db.relationship("Booking", backref=db.backref("payment", uselist=False))

    __table_args__ = (
        db.CheckConstraint("amount >= 0", name="ck_payment_amount_not_negative"),
    )

    def __repr__(self):
        return f"<Payment {self.receipt_number or self.id} {self.method} {self.status}>"