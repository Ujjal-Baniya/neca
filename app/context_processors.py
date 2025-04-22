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