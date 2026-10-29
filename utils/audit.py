from flask import request
from flask_login import current_user

from extensions import db
from models.audit import AuditLog


def log_action(action, target_type, target_id, details=None):
    db.session.add(AuditLog(
        admin_id=current_user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=(details or "")[:300] or None,
        ip_address=request.remote_addr,
    ))