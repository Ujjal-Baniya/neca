# Create a file named add_categories.py in your project root
from app import create_app, db
from app.models.service import ServiceCategory

app = create_app()

with app.app_context():
    # Check if categories already exist
    if ServiceCategory.query.count() == 0:
        # Define default categories
        default_categories = [
            {"name": "Home Improvement", "description": "Services related to home repairs, renovations, and maintenance"},
            {"name": "Professional Services", "description": "Legal, financial, consulting, and other professional services"},
            {"name": "Technology", "description": "Computer repair, IT support, web development, and tech services"},
            {"name": "Health & Wellness", "description": "Fitness, nutrition, counseling, and wellness services"},
            {"name": "Education & Tutoring", "description": "Teaching, tutoring, and educational support"},
            {"name": "Creative Services", "description": "Graphic design, photography, writing, and artistic services"},
            {"name": "Events & Entertainment", "description": "Event planning, music, performances, and entertainment"},
            {"name": "Transportation", "description": "Moving, delivery, and transportation services"},
            {"name": "Beauty & Personal Care", "description": "Haircuts, styling, makeup, and personal care services"},
            {"name": "Cleaning & Maintenance", "description": "Cleaning, landscaping, and property maintenance"},
            {"name": "Other", "description": "Other services not fitting into the above categories"}
        ]
        
        # Add categories to database
        for category_data in default_categories:
            category = ServiceCategory(**category_data)
            db.session.add(category)
            print(f"Added category: {category_data['name']}")
        
        db.session.commit()
        print("Default categories added successfully!")
    else:
        print("Categories already exist in the database")