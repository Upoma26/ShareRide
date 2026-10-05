import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "shareride.sqlite3"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "nid")
    ALLOWED_NID_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)