from datetime import datetime

from extensions import db

CHAT_OPEN_HOURS = 24
MAX_MESSAGE_LENGTH = 500


class Message(db.Model):
    _tablename_ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    body = db.Column(db.String(MAX_MESSAGE_LENGTH), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    ride = db.relationship("Ride", backref=db.backref("messages", lazy="dynamic"))
    sender = db.relationship("User")

    def to_dict(self, viewer_id):
        return {
            "id": self.id,
            "sender": self.sender.full_name,
            "mine": self.sender_id == viewer_id,
            "is_driver": self.sender_id == self.ride.provider_id,
            "body": self.body,
            "time": self.created_at.strftime("%d %b, %I:%M %p"),
        }