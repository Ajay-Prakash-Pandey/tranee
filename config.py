import os
import tempfile
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = Path(tempfile.gettempdir()) / "backend_assignment_app.db"

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key-change-me-1234567890')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-super-secret-key-change-me-1234567890')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
