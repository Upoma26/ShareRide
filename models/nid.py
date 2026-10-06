from datetime import datetime

from extensions import db


class NidReview(db.Model):
    __tablename__ = "nid_reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    decision = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id], backref="nid_reviews")
    admin = db.relationship("User", foreign_keys=[admin_id])


class NidAccessLog(db.Model):
    __tablename__ = "nid_access_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    side = db.Column(db.String(10), nullable=False)
    ip_address = db.Column(db.String(45))
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])
    admin = db.relationship("User", foreign_keys=[admin_id])