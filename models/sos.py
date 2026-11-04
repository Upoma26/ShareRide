from datetime import datetime

from extensions import db


class SosAlert(db.Model):
    __tablename__ = "sos_alerts"

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    message = db.Column(db.String(300))

    status = db.Column(db.String(20), nullable=False, default="open")
    created_at = db.Column(db.DateTime, default=datetime.now)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    ride = db.relationship("Ride", backref="sos_alerts")
    user = db.relationship("User", foreign_keys=[user_id])
    resolver = db.relationship("User", foreign_keys=[resolved_by])

    @property
    def latest_location(self):
        return self.locations.order_by(SosLocation.id.desc()).first()


class SosLocation(db.Model):
    __tablename__ = "sos_locations"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("sos_alerts.id"), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.now)

    alert = db.relationship("SosAlert", backref=db.backref("locations", lazy="dynamic"))