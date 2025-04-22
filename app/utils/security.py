"""Security utilities."""
import os
import uuid
from flask import current_app

def generate_random_filename(original_filename):
    """Generate a random filename while preserving the original extension."""
    _, ext = os.path.splitext(original_filename)
    return str(uuid.uuid4()) + ext

def allowed_file(filename):
    """Check if file has an allowed extension."""
    if not filename:
        return False
    
    ext = os.path.splitext(filename)[1].lower()[1:]  # Get extension without dot
    return ext in current_app.config["ALLOWED_EXTENSIONS"]

def secure_filename_with_extension(filename):
    """Generate a secure filename that preserves the original extension."""
    from werkzeug.utils import secure_filename
    
    secured = secure_filename(filename)
    if not secured:
        return None
    
    return secured