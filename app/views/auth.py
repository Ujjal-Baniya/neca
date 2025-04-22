"""Authentication views."""
import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

from app.extensions import db, bcrypt, google_blueprint
from app.forms.auth import LoginForm, RegistrationForm, ProfileForm
from app.models.user import User, Role, UserRole
from app.utils.security import generate_random_filename, allowed_file

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data if form.phone.data else None,
            active=True
        )
        user.set_password(form.password.data)
        
        # Add user to database
        db.session.add(user)
        db.session.commit()
        
        # Add roles
        if form.is_seller.data:
            _add_role_to_user(user, 'seller')
        
        if form.is_consumer.data:
            _add_role_to_user(user, 'consumer')
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Log in a user."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.active:
                flash('This account has been deactivated.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            user.last_seen = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out a user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page."""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Update user data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.bio = form.bio.data
        
        # Update roles
        if form.is_seller.data and not current_user.is_seller:
            _add_role_to_user(current_user, 'seller')
        elif not form.is_seller.data and current_user.is_seller:
            _remove_role_from_user(current_user, 'seller')
        
        if form.is_consumer.data and not current_user.is_consumer:
            _add_role_to_user(current_user, 'consumer')
        elif not form.is_consumer.data and current_user.is_consumer:
            _remove_role_from_user(current_user, 'consumer')
        
        # Handle profile image upload
        if form.profile_image.data:
            if _save_profile_image(form.profile_image.data):
                flash('Profile image uploaded successfully.', 'success')
            else:
                flash('Error uploading profile image.', 'danger')
        
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('auth.profile'))
    
    # Pre-fill role checkboxes
    form.is_seller.data = current_user.is_seller
    form.is_consumer.data = current_user.is_consumer
    
    return render_template('auth/profile.html', form=form)

@auth_bp.route('/google-login')
def google_login():
    """Initiate Google OAuth login."""
    if not google_blueprint.session.token:
        return redirect(url_for('google.login'))
    return redirect(url_for('auth.google_login_callback'))

@auth_bp.route('/google-login/callback')
def google_login_callback():
    """Handle Google OAuth callback."""
    if not google_blueprint.session.token:
        flash('Failed to log in with Google.', 'danger')
        return redirect(url_for('auth.login'))
    
    resp = google_blueprint.session.get('/oauth2/v1/userinfo')
    if not resp.ok:
        flash('Failed to get user info from Google.', 'danger')
        return redirect(url_for('auth.login'))
    
    google_info = resp.json()
    google_id = google_info['id']
    
    # Check if user exists
    user = User.query.filter_by(google_id=google_id).first()
    
    if not user:
        # Check if email exists
        user = User.query.filter_by(email=google_info['email']).first()
        
        if user:
            # Link Google ID to existing account
            user.google_id = google_id
        else:
            # Create new user
            user = User(
                username=google_info.get('name', '').replace(' ', '_').lower() + str(google_id)[-5:],
                email=google_info['email'],
                google_id=google_id,
                active=True
            )
            db.session.add(user)
            
            # Add default consumer role
            _add_role_to_user(user, 'consumer')
    
    # Update profile image if needed
    if google_info.get('picture') and not user.profile_image:
        user.profile_image = google_info['picture']
    
    user.last_seen = datetime.utcnow()
    db.session.commit()
    
    login_user(user)
    flash('You have been logged in with Google.', 'success')
    
    next_page = request.args.get('next')
    if next_page:
        return redirect(next_page)
    return redirect(url_for('main.index'))

def _add_role_to_user(user, role_name):
    """Add a role to a user."""
    role = Role.query.filter_by(name=role_name).first()
    if role and role not in user.roles:
        try:
            user_role = UserRole(user_id=user.id, role_id=role.id)
            db.session.add(user_role)
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
    return False

def _remove_role_from_user(user, role_name):
    """Remove a role from a user."""
    role = Role.query.filter_by(name=role_name).first()
    if role and role in user.roles:
        user_role = UserRole.query.filter_by(user_id=user.id, role_id=role.id).first()
        if user_role:
            db.session.delete(user_role)
            db.session.commit()
            return True
    return False

def _save_profile_image(image_data):
    """Save profile image to disk."""
    if not allowed_file(image_data.filename):
        return False
    
    filename = secure_filename(image_data.filename)
    random_filename = generate_random_filename(filename)
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
    
    try:
        # Save the image
        image_path = os.path.join(upload_folder, random_filename)
        image_data.save(image_path)
        
        # Update user profile
        if current_user.profile_image and os.path.exists(os.path.join(upload_folder, current_user.profile_image)):
            os.remove(os.path.join(upload_folder, current_user.profile_image))
        
        current_user.profile_image = random_filename
        return True
    except Exception as e:
        current_app.logger.error(f"Error saving profile image: {e}")
        return False