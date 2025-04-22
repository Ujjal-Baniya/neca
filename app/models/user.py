"""User models."""
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func

from app.extensions import db, bcrypt

# Association table for user roles
class UserRole(db.Model):
    """Association between users and roles."""
    
    __tablename__ = "user_roles"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate role assignments
    __table_args__ = (db.UniqueConstraint("user_id", "role_id", name="uq_user_role"),)
    
    def __repr__(self):
        return f"<UserRole {self.user_id}:{self.role_id}>"

# Saved services association table
saved_services = db.Table(
    "saved_services",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("service_id", db.Integer, db.ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow)
)

class Role(db.Model):
    """User role model."""
    
    __tablename__ = "roles"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship("User", secondary="user_roles", back_populates="roles")
    
    def __repr__(self):
        return f"<Role {self.name}>"

class User(UserMixin, db.Model):
    """User model."""
    
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password = db.Column("password", db.String(128))
    phone = db.Column(db.String(15), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    active = db.Column(db.Boolean(), default=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # OAuth related fields
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    
    # Relationships
    roles = db.relationship("Role", secondary="user_roles", back_populates="users")
    services = db.relationship("Service", back_populates="seller", lazy="dynamic")
    saved_services_rel = db.relationship("Service", secondary=saved_services, back_populates="saved_by_users")
    reviews_given = db.relationship("Review", foreign_keys="Review.reviewer_id", back_populates="reviewer", lazy="dynamic")
    reviews_received = db.relationship("Review", foreign_keys="Review.reviewee_id", back_populates="reviewee", lazy="dynamic")
    sent_messages = db.relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", lazy="dynamic")
    received_messages = db.relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient", lazy="dynamic")
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic")
    
    @hybrid_property
    def password(self):
        """Prevent password from being accessed."""
        raise AttributeError("password is not a readable attribute")
    
    @password.setter
    def password(self, value):
        """Hash password on save."""
        self._password = bcrypt.generate_password_hash(value).decode("utf-8")
    
    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self._password, value)
    
    def set_password(self, password):
        """Set password."""
        self.password = password
    
    @property
    def is_admin(self):
        """Check if user has admin role."""
        return any(role.name == "admin" for role in self.roles)
    
    @property
    def is_seller(self):
        """Check if user has seller role."""
        return any(role.name == "seller" for role in self.roles)
    
    @property
    def is_consumer(self):
        """Check if user has consumer role."""
        return any(role.name == "consumer" for role in self.roles)
    
    def add_role(self, role_name):
        """Add a role to user."""
        role = Role.query.filter_by(name=role_name).first()
        if role and role not in self.roles:
            user_role = UserRole(user_id=self.id, role_id=role.id)
            db.session.add(user_role)
            db.session.commit()
    
    def remove_role(self, role_name):
        """Remove a role from user."""
        role = Role.query.filter_by(name=role_name).first()
        if role and role in self.roles:
            user_role = UserRole.query.filter_by(user_id=self.id, role_id=role.id).first()
            if user_role:
                db.session.delete(user_role)
                db.session.commit()
    
    def save_service(self, service):
        """Save a service."""
        if service not in self.saved_services_rel:
            self.saved_services_rel.append(service)
            db.session.commit()
    
    def unsave_service(self, service):
        """Unsave a service."""
        if service in self.saved_services_rel:
            self.saved_services_rel.remove(service)
            db.session.commit()
    
    def has_saved_service(self, service):
        """Check if user has saved a service."""
        return service in self.saved_services_rel
    
    @property
    def avg_rating(self):
        """Calculate average rating for user."""
        from app.models.review import Review
        result = db.session.query(func.avg(Review.rating)).filter(Review.reviewee_id == self.id).scalar()
        return round(result, 1) if result else None
    
    @property
    def review_count(self):
        """Count reviews for user."""
        return self.reviews_received.count()
    
    @property
    def unread_message_count(self):
        """Count unread messages."""
        return self.received_messages.filter_by(read=False).count()
    
    @property
    def unread_notification_count(self):
        """Count unread notifications."""
        return self.notifications.filter_by(read=False).count()
    
    def __repr__(self):
        return f"<User {self.username}>"