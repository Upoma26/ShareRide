from flask import Flask

from config import Config
from extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from models.user import User  # noqa: F401
    from models.otp import OTP  # noqa: F401

    from routes.main import main_bp
    app.register_blueprint(main_bp)
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Database tables created.")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)