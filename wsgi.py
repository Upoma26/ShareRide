import os

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(_file_))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app import app as application