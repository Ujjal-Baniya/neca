"""CLI commands for the Flask application."""
import os
import click
from flask.cli import with_appcontext
from flask import current_app

from app.extensions import db
from app.models.user import User, Role, UserRole

def register_commands(app):
    """Register CLI commands."""
    app.cli.add_command(create_db)
    app.cli.add_command(drop_db)
    app.cli.add_command(init_db)
    app.cli.add_command(create_admin)

@click.command("create-db")
@with_appcontext
def create_db():
    """Create the database tables."""
    db.create_all()
    click.echo("Created database tables.")

@click.command("drop-db")
@with_appcontext
def drop_db():
    """Drop the database tables."""
    if click.confirm("Are you sure you want to drop all tables?"):
        db.drop_all()
        click.echo("Dropped database tables.")

@click.command("init-db")
@with_appcontext
def init_db():
    """Initialize the database with required data."""
    # Create user roles
    _create_roles()
    click.echo("Initialized database with required data.")

@click.command("create-admin")
@click.option("--email", prompt=True, help="Admin email address")
@click.option("--username", prompt=True, help="Admin username")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Admin password")
@with_appcontext
def create_admin(email, username, password):
    """Create an admin user."""
    # Check if admin role exists
    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="Administrator")
        db.session.add(admin_role)
        db.session.commit()
    
    # Create the user
    user = User(
        email=email,
        username=username,
        active=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # Assign admin role
    user_role = UserRole(user_id=user.id, role_id=admin_role.id)
    db.session.add(user_role)
    db.session.commit()
    
    click.echo(f"Created admin user: {email}")

def _create_roles():
    """Create default roles."""
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
    
    db.session.commit()
    
    # Create upload directories
    _create_upload_dirs()

def _create_upload_dirs():
    """Create upload directories."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    subdirs = ["services", "profiles", "reviews"]
    
    for subdir in subdirs:
        directory = os.path.join(upload_folder, subdir)
        os.makedirs(directory, exist_ok=True)