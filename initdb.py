from app import create_app, db
from app.models.user import User, Role, UserRole
from app.models.service import Service, ServiceCategory, ServiceImage
from app.models.review import Review, ReviewImage
from app.models.message import Message, Conversation
from app.models.notification import Notification

app = create_app()

with app.app_context():
    # Drop all existing tables
    print("Dropping existing tables...")
    db.drop_all()
    
    # Create tables
    print("Creating database tables...")
    db.create_all()
    
    # Create default roles
    roles = [
        {"name": "admin", "description": "Administrator"},
        {"name": "consumer", "description": "Service Consumer"},
        {"name": "seller", "description": "Service Provider"}
    ]
    
    for role_data in roles:
        role = Role.query.filter_by(name=role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            db.session.add(role)
            print(f"Created role: {role_data['name']}")
    
    db.session.commit()
    print("Database initialization complete!")