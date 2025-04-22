"""Notification models."""
from datetime import datetime

from app.extensions import db

class Notification(db.Model):
    """Notification model for user events."""
    
    __tablename__ = "notifications"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # message, review, service_inquiry
    content = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.Integer, nullable=True)  # ID of the related object (e.g., message, review)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", back_populates="notifications")
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.read:
            self.read = True
            db.session.commit()
    
    @classmethod
    def create(cls, user_id, type, content, related_id=None):
        """Create a new notification."""
        notification = cls(
            user_id=user_id,
            type=type,
            content=content,
            related_id=related_id
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @classmethod
    def mark_all_as_read(cls, user_id):
        """Mark all notifications for a user as read."""
        cls.query.filter_by(user_id=user_id, read=False).update({cls.read: True})
        db.session.commit()
    
    def __repr__(self):
        return f"<Notification {self.id}: {self.type}>"