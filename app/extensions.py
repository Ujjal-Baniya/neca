"""Extensions module."""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_admin import Admin
from flask_socketio import SocketIO
from flask_dance.contrib.google import make_google_blueprint

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
admin = Admin(name="ServiceMarketplace Admin", template_mode="bootstrap4")
socketio = SocketIO()

# Create Google OAuth blueprint
google_blueprint = make_google_blueprint(
    scope=["profile", "email"],
    redirect_to="auth.google_login_callback"
)