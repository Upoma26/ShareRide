from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please sign in first.", "warning")
                return redirect(url_for("auth.login"))

            if current_user.role not in roles:
                flash("You do not have permission to open that page.", "danger")
                return redirect(url_for("main.index"))

            return view(*args, **kwargs)
        return wrapped
    return decorator