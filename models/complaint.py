from datetime import datetime

from extensions import db

COMPLAINT_CATEGORIES = {
    "safety": "Safety concern",
    "behaviour": "Rude or unsafe behaviour",
    "payment": "Payment or fare issue",
    "vehicle": "Vehicle condition",
    "no_show": "No-show or very late",
    "other": "Other",
}

COMPLAINT_STATUSES = ("open", "investigating", "resolved", "dismissed")


class Complaint(db.Model):
    _tablename_ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    complainant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    against_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"))

    category = db.Column(db.String(30), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), nullable=False, default="open")
    admin_note = db.Column(db.String(500))
    action_taken = db.Column(db.String(20))
    handled_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    complainant = db.relationship("User", foreign_keys=[complainant_id])
    against = db.relationship("User", foreign_keys=[against_id])
    handler = db.relationship("User", foreign_keys=[handled_by])
    ride = db.relationship("Ride", backref="complaints")

    @property
    def category_label(self):
        return COMPLAINT_CATEGORIES.get(self.category, self.category)

    @property
    def is_open(self):
        return self.status in ("open", "investigating")