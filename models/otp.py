import secrets
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db

OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_SECONDS = 60


class OTP(db.Model):
    __tablename__ = "otps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    code_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_code():
        return f"{secrets.randbelow(1000000):06d}"

    def set_code(self, code):
        self.code_hash = generate_password_hash(code)
        self.expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    def check_code(self, code):
        return check_password_hash(self.code_hash, code)

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    @property
    def is_locked(self):
        return self.attempts >= OTP_MAX_ATTEMPTS