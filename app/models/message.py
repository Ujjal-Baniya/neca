"""Message models."""
from datetime import datetime

from app.extensions import db

class Conversation(db.Model):
    """Conversation model between two users."""
    
    __tablename__ = "conversations"
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user1 = db.relationship("User", foreign_keys=[user1_id])
    user2 = db.relationship("User", foreign_keys=[user2_id])
    messages = db.relationship("Message", back_populates="conversation", lazy="dynamic",
                             cascade="all, delete-orphan", order_by="Message.created_at")
    
    # Ensure a conversation between the same two users is unique
    # (regardless of who is user1 and who is user2)
    __table_args__ = (
        db.UniqueConstraint("user1_id", "user2_id", name="uq_conversation_users"),
    )
    
    @classmethod
    def get_or_create(cls, user1_id, user2_id):
        """Get an existing conversation or create a new one."""
        # Ensure users are ordered consistently to maintain uniqueness
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
            
        conversation = cls.query.filter(
            (cls.user1_id == user1_id) & (cls.user2_id == user2_id)
        ).first()
        
        if not conversation:
            conversation = cls(user1_id=user1_id, user2_id=user2_id)
            db.session.add(conversation)
            db.session.commit()
            
        return conversation
    
    def get_other_user(self, user_id):
        """Get the other user in the conversation."""
        return self.user2 if self.user1_id == user_id else self.user1
    
    def has_user(self, user_id):
        """Check if a user is part of this conversation."""
        return self.user1_id == user_id or self.user2_id == user_id
    
    def __repr__(self):
        return f"<Conversation {self.id}: {self.user1_id} - {self.user2_id}>"

class Message(db.Model):
    """Message model between users."""
    
    __tablename__ = "messages"
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = db.relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")
    conversation = db.relationship("Conversation", back_populates="messages")
    
    def mark_as_read(self):
        """Mark message as read."""
        if not self.read:
            self.read = True
            db.session.commit()
    
    def is_owner(self, user):
        """Check if user is the owner of this message."""
        return user and self.sender_id == user.id
    
    def __repr__(self):
        return f"<Message {self.id}: {self.sender_id} -> {self.recipient_id}>"