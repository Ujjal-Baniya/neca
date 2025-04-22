"""Notification views."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.notification import Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/')
@login_required
def index():
    """View all notifications."""
    page = request.args.get('page', 1, type=int)
    notifications = current_user.notifications.order_by(Notification.created_at.desc()) \
        .paginate(page=page, per_page=20)
    
    return render_template('notifications/index.html', notifications=notifications)

@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark a notification as read."""
    notification = Notification.query.get_or_404(notification_id)
    
    # Ensure user owns the notification
    if notification.user_id != current_user.id:
        abort(403)
    
    notification.mark_as_read()
    
    # Check if request is AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    Notification.mark_all_as_read(current_user.id)
    
    flash('All notifications marked as read.', 'success')
    
    # Check if request is AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete(notification_id):
    """Delete a notification."""
    notification = Notification.query.get_or_404(notification_id)
    
    # Ensure user owns the notification
    if notification.user_id != current_user.id:
        abort(403)
    
    db.session.delete(notification)
    db.session.commit()
    
    # Check if request is AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    flash('Notification deleted.', 'success')
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/delete-all', methods=['POST'])
@login_required
def delete_all():
    """Delete all notifications."""
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    flash('All notifications deleted.', 'success')
    
    # Check if request is AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/get-unread-count')
@login_required
def get_unread_count():
    """Get the number of unread notifications."""
    count = current_user.unread_notification_count
    
    return jsonify({'count': count})