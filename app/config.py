import os
from datetime import timedelta

class Config:
    """Base configuration."""
    
    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "default-dev-key-change-in-production")
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(PROJECT_ROOT, "servicemarketplace.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(APP_DIR, "static", "uploads"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    
    # Authentication settings
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    
    # Pagination settings
    SERVICES_PER_PAGE = 12
    REVIEWS_PER_PAGE = 10
    MESSAGES_PER_PAGE = 20
    
    # Socket.IO settings
    SOCKETIO_ASYNC_MODE = os.environ.get("SOCKETIO_ASYNC_MODE", "eventlet")
    CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_MESSAGE_QUEUE = None  # Use Redis in production: "redis://"

class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False

class DevConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProdConfig(Config):
    """Production configuration."""
    DEBUG = False
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CORS_ALLOWED_ORIGINS = ["https://yourwebsite.com"]
    
    # Use Redis for Socket.IO message queue in production
    SOCKETIO_MESSAGE_QUEUE = os.environ.get("REDIS_URL", "redis://")