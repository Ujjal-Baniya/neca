"""Main routes."""
from flask import Blueprint, render_template, request, current_app
from flask_login import current_user
from app.extensions import db

from app.models.service import Service, ServiceCategory
from app.forms.service import ServiceSearchForm

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render homepage."""
    page = request.args.get('page', 1, type=int)
    
    # Get featured services
    featured_services = Service.query.filter_by(active=True) \
        .order_by(Service.created_at.desc()) \
        .paginate(page=page, per_page=current_app.config['SERVICES_PER_PAGE'])
    
    # Get latest services
    latest_services = Service.query.filter_by(active=True) \
        .order_by(Service.created_at.desc()) \
        .limit(4).all()
    
    # Get categories for filtering
    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()
    
    # Initialize search form
    search_form = ServiceSearchForm()
    
    return render_template('index.html',
                          featured_services=featured_services,
                          latest_services=latest_services,
                          categories=categories,
                          search_form=search_form)

from flask_login import current_user
from app.extensions import db
from datetime import datetime

def utility_processor():
    """Add utility functions/variables to template context."""
    
    def user_has_unread_notifications():
        """Check if current user has unread notifications."""
        if current_user.is_authenticated:
            return current_user.unread_notification_count > 0
        return False
    
    def user_has_unread_messages():
        """Check if current user has unread messages."""
        if current_user.is_authenticated:
            return current_user.unread_message_count > 0
        return False
    
    def unread_notifications_count():
        """Return count of unread notifications."""
        if current_user.is_authenticated:
            return current_user.unread_notification_count
        return 0
    
    def unread_messages_count():
        """Return count of unread messages."""
        if current_user.is_authenticated:
            return current_user.unread_message_count
        return 0
    
    return dict(
        now=datetime.now(),
        db=db,
        user_has_unread_notifications=user_has_unread_notifications,
        user_has_unread_messages=user_has_unread_messages,
        unread_notifications_count=unread_notifications_count,
        unread_messages_count=unread_messages_count
    )
@main_bp.route('/about')
def about():
    """Render about page."""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Render contact page."""
    return render_template('contact.html')

@main_bp.route('/terms')
def terms():
    """Render terms of service page."""
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    """Render privacy policy page."""
    return render_template('privacy.html')

@main_bp.app_errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors."""
    return render_template('errors/500.html'), 500

@main_bp.context_processor
def utility_processor():
    """Add utility functions/variables to template context."""
    def user_has_unread_notifications():
        """Check if current user has unread notifications."""
        if current_user.is_authenticated:
            return current_user.unread_notification_count > 0
        return False
    
    def user_has_unread_messages():
        """Check if current user has unread messages."""
        if current_user.is_authenticated:
            return current_user.unread_message_count > 0
        return False
    
    def unread_notifications_count():
        """Return count of unread notifications."""
        if current_user.is_authenticated:
            return current_user.unread_notification_count
        return 0
    
    def unread_messages_count():
        """Return count of unread messages."""
        if current_user.is_authenticated:
            return current_user.unread_message_count
        return 0
    
    return dict(
        user_has_unread_notifications=user_has_unread_notifications,
        user_has_unread_messages=user_has_unread_messages,
        unread_notifications_count=unread_notifications_count,
        unread_messages_count=unread_messages_count
    )