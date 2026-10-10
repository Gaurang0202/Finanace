"""
config.py
---------
Central configuration for the Personal Finance Dashboard.

All secrets and environment-specific values are pulled from a `.env` file
(see .env.example) so nothing sensitive is hard-coded into source control.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # --- Database -------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        f"sqlite:///{os.path.join(BASE_DIR, 'database', 'finance.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Auth / Sessions --------------------------------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    WTF_CSRF_TIME_LIMIT = None

    # --- Mail -------------------------------------------------------------
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # --- Admin bootstrap ----------------------------------------------------
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@12345")

    # --- Uploads --------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

    # --- Budget alert thresholds ---------------------------------------
    BUDGET_WARN_THRESHOLD = 0.8   # 80%
    BUDGET_CRITICAL_THRESHOLD = 1.0  # 100%


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
