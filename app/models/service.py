"""Service models."""
from datetime import datetime
from sqlalchemy import func

from app.extensions import db
from app.models.user import saved_services

class ServiceCategory(db.Model):
    """Service category model."""
    
    __tablename__ = "service_categories"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    services = db.relationship("Service", back_populates="category", lazy="dynamic")
    
    def __repr__(self):
        return f"<ServiceCategory {self.name}>"

class ServiceImage(db.Model):
    """Service image model."""
    
    __tablename__ = "service_images"
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service = db.relationship("Service", back_populates="images")
    
    def __repr__(self):
        return f"<ServiceImage {self.filename}>"

class Service(db.Model):
    """Service model."""
    
    __tablename__ = "services"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    price_type = db.Column(db.String(20), nullable=False, default="hourly")  # hourly or fixed
    location = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("service_categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = db.relationship("User", back_populates="services")
    category = db.relationship("ServiceCategory", back_populates="services")
    images = db.relationship("ServiceImage", back_populates="service", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="service", cascade="all, delete-orphan", lazy="dynamic")
    saved_by_users = db.relationship("User", secondary=saved_services, back_populates="saved_services_rel")
    
    @property
    def primary_image(self):
        """Get the primary image for the service."""
        primary = next((img for img in self.images if img.primary), None)
        if primary:
            return primary
        # Return the first image if no primary is set
        return self.images[0] if self.images else None
    
    @property
    def avg_rating(self):
        """Calculate average rating for service."""
        from app.models.review import Review
        result = db.session.query(func.avg(Review.rating)).filter(Review.service_id == self.id).scalar()
        return round(result, 1) if result else None
    
    @property
    def review_count(self):
        """Count reviews for service."""
        return self.reviews.count()
    
    def is_owner(self, user):
        """Check if user is the owner of this service."""
        return user and self.seller_id == user.id
    
    def __repr__(self):
        return f"<Service {self.title}>"