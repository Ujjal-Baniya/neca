"""User profile views."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user

from app.models.user import User
from app.models.service import Service
from app.models.review import Review
from app.forms.message import MessageForm
from app.extensions import db


profiles_bp = Blueprint('profiles', __name__)

@profiles_bp.route('/<int:user_id>')
def view(user_id):
    """View a user's profile."""
    user = User.query.get_or_404(user_id)
    
    # Get user's services if they are a seller
    services = None
    if user.is_seller:
        services = Service.query.filter_by(seller_id=user_id, active=True) \
            .order_by(Service.created_at.desc()).limit(4).all()
    
    # Get reviews for this user
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.filter_by(reviewee_id=user_id) \
        .order_by(Review.created_at.desc()) \
        .paginate(page=page, per_page=current_app.config['REVIEWS_PER_PAGE'])
    
    # Initialize message form if user is authenticated
    message_form = None
    if current_user.is_authenticated and current_user.id != user_id:
        message_form = MessageForm()
        message_form.recipient_id.data = user_id
    
    return render_template('profiles/view.html',
                          user=user,
                          services=services,
                          reviews=reviews,
                          message_form=message_form)

@profiles_bp.route('/sellers')
def sellers():
    """View all sellers."""
    page = request.args.get('page', 1, type=int)
    
    # Get users with seller role
    from app.models.user import UserRole, Role
    
    seller_role = Role.query.filter_by(name='seller').first()
    if not seller_role:
        abort(404)
    
    sellers = User.query.join(UserRole).filter(
        UserRole.role_id == seller_role.id,
        User.active == True
    ).order_by(User.username).paginate(page=page, per_page=20)
    
    return render_template('profiles/sellers.html', sellers=sellers)

@profiles_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    # Get user's services if they are a seller
    services = None
    if current_user.is_seller:
        services = Service.query.filter_by(seller_id=current_user.id) \
            .order_by(Service.created_at.desc()).all()
    
    # Get user's saved services
    saved_services = current_user.saved_services_rel
    
    # Get unread messages
    unread_messages = current_user.received_messages.filter_by(read=False) \
        .order_by(db.text('created_at DESC')).limit(5).all()
    
    # Get unread notifications
    unread_notifications = current_user.notifications.filter_by(read=False) \
        .order_by(db.text('created_at DESC')).limit(5).all()
    
    # Get reviews received
    reviews_received = current_user.reviews_received.order_by(db.text('created_at DESC')).limit(5).all()
    
    return render_template('profiles/dashboard.html',
                          services=services,
                          saved_services=saved_services,
                          unread_messages=unread_messages,
                          unread_notifications=unread_notifications,
                          reviews_received=reviews_received)