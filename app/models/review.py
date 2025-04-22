"""Review models."""
from datetime import datetime

from app.extensions import db

class ReviewImage(db.Model):
    """Review image model."""
    
    __tablename__ = "review_images"
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    review = db.relationship("Review", back_populates="images")
    
    def __repr__(self):
        return f"<ReviewImage {self.filename}>"

class Review(db.Model):
    """Review model for services and users."""
    
    __tablename__ = "reviews"
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id", ondelete="CASCADE"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviewer = db.relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewee = db.relationship("User", foreign_keys=[reviewee_id], back_populates="reviews_received")
    service = db.relationship("Service", back_populates="reviews")
    images = db.relationship("ReviewImage", back_populates="review", cascade="all, delete-orphan")
    
    # Ensure a user can only review a service once
    __table_args__ = (
        db.UniqueConstraint("reviewer_id", "service_id", name="uq_reviewer_service"),
    )
    
    def is_owner(self, user):
        """Check if user is the owner of this review."""
        return user and self.reviewer_id == user.id
    
    def __repr__(self):
        return f"<Review {self.id}: {self.rating}/5>"