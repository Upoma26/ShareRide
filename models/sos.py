from datetime import datetime

from extensions import db


class SosAlert(db.Model):
    _tablename_ = "sos_alerts"

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    message = db.Column(db.String(300))

    status = db.Column(db.String(20), nullable=False, default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    ride = db.relationship("Ride", backref="sos_alerts")
    user = db.relationship("User", foreign_keys=[user_id])
    resolver = db.relationship("User", foreign_keys=[resolved_by])