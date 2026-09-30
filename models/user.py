from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="seeker")

    nid_number = db.Column(db.String(30), unique=True, nullable=False)
    nid_document = db.Column(db.String(255))

    phone_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(20), default="pending")
    account_status = db.Column(db.String(20), default="active")

    rating = db.Column(db.Float, default=0.0)
    total_trips = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_verified(self):
        return self.verification_status == "verified"

    @property
    def is_active_account(self):
        return self.account_status == "active"

    def _repr_(self):
        return f"<User {self.full_name} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))