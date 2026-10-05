import time

from flask import Flask, session, flash, redirect, url_for
from flask_login import current_user, logout_user

from config import Config
from extensions import db, login_manager

ADMIN_TIMEOUT_MINUTES = 20
USER_TIMEOUT_MINUTES = 30


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in first."
    login_manager.login_message_category = "warning"

    from models.user import User  # noqa: F401
    from models.otp import OTP  # noqa: F401
    from models.vehicle import Vehicle  # noqa: F401
    from models.ride import Ride  # noqa: F401

    from routes.main import main_bp
    app.register_blueprint(main_bp)
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    @app.before_request
    def check_session_timeout():
        if not current_user.is_authenticated:
            return None

        if current_user.role == "admin":
            limit = ADMIN_TIMEOUT_MINUTES * 60
        else:
            limit = USER_TIMEOUT_MINUTES * 60

        now = time.time()
        last_seen = session.get("last_seen", now)

        if now - last_seen > limit:
            logout_user()
            session.pop("last_seen", None)
            flash("You were signed out after a period of inactivity.", "warning")
            return redirect(url_for("auth.login"))

        session["last_seen"] = now
        return None

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Database tables created.")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)