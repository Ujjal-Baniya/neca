import os
from flask import Flask
from dotenv import load_dotenv
from datetime import datetime

from app.extensions import db, migrate, login_manager, bcrypt, csrf, admin, socketio
from app.commands import register_commands

# Load environment variables from .env file
load_dotenv()


def create_app(config_object="app.config.Config"):
    """Create application factory."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # Ensure instance path exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize extensions
    register_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register CLI commands
    register_commands(app)
    
    # Register error handlers
    register_errorhandlers(app)
    
    # Configure admin views
    configure_admin(app)
    
    # Configure Socket.IO handlers
    configure_socketio()
    # Add Jinja2 filters
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if not s:
            return s
        return s.replace('\n', '<br>')
    
    @app.context_processor

    def inject_now():
        return {'now': datetime.now()}
    
     # Register global context processors
    from app.context_processors import utility_processor
    app.context_processor(utility_processor)

    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    
    subdirs = ['profiles', 'services', 'reviews']
    for subdir in subdirs:
        directory = os.path.join(upload_folder, subdir)
        os.makedirs(directory, exist_ok=True)
    
    return app

def register_extensions(app):
    """Register Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    admin.init_app(app)
    socketio.init_app(app, async_mode=app.config['SOCKETIO_ASYNC_MODE'], 
                     cors_allowed_origins=app.config['CORS_ALLOWED_ORIGINS'],
                     message_queue=app.config.get('SOCKETIO_MESSAGE_QUEUE'))
    
    # Configure login manager
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    
    return None

def register_blueprints(app):
    """Register Flask blueprints."""
    from app.views.main import main_bp
    from app.views.auth import auth_bp
    from app.views.services import services_bp
    from app.views.reviews import reviews_bp
    from app.views.messages import messages_bp
    from app.views.notifications import notifications_bp
    from app.views.profiles import profiles_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(services_bp, url_prefix='/services')
    app.register_blueprint(reviews_bp, url_prefix='/reviews')
    app.register_blueprint(messages_bp, url_prefix='/messages')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(profiles_bp, url_prefix='/profiles')
    
    return None

def register_errorhandlers(app):
    """Register error handlers."""
    from flask import render_template
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500
    
    return None

def configure_admin(app):
    """Configure admin views."""
    from app.views.admin import configure_admin_views
    configure_admin_views(admin, db)
    
    return None

def configure_socketio():
    """Configure Socket.IO event handlers."""
    from app.views.messages import register_socketio_handlers
    register_socketio_handlers(socketio)
    
    return None