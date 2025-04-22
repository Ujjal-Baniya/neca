"""Image processing utilities."""
import os
from io import BytesIO
from PIL import Image, ExifTags
from flask import current_app

def resize_image(image_data, max_size=(800, 800), quality=85, format="JPEG"):
    """Resize an image while maintaining aspect ratio."""
    img = Image.open(image_data)
    
    # Handle image rotation based on EXIF data
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        
        exif = dict(img._getexif().items())
        
        if exif[orientation] == 2:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        elif exif[orientation] == 3:
            img = img.rotate(180, expand=True)
        elif exif[orientation] == 4:
            img = img.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
        elif exif[orientation] == 5:
            img = img.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
        elif exif[orientation] == 6:
            img = img.rotate(-90, expand=True)
        elif exif[orientation] == 7:
            img = img.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
        elif exif[orientation] == 8:
            img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # No EXIF data or no orientation info
        pass
    
    # Calculate new dimensions
    width, height = img.size
    if width > max_size[0] or height > max_size[1]:
        # Calculate aspect ratio
        ratio = min(max_size[0] / width, max_size[1] / height)
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Save to BytesIO
    output = BytesIO()
    img.save(output, format=format, quality=quality)
    output.seek(0)
    
    return output

def create_thumbnail(image_data, size=(200, 200), quality=85, format="JPEG"):
    """Create a thumbnail from an image."""
    img = Image.open(image_data)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Create thumbnail
    img.thumbnail(size, Image.LANCZOS)
    
    # Save to BytesIO
    output = BytesIO()
    img.save(output, format=format, quality=quality)
    output.seek(0)
    
    return output

def process_and_save_image(image_file, upload_path, filename, create_thumb=False, thumb_size=(200, 200)):
    """Process and save an image with optional thumbnail creation."""
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    
    # Resize the original image
    img_io = resize_image(image_file)
    
    # Save the resized image
    with open(os.path.join(upload_path, filename), 'wb') as f:
        f.write(img_io.getvalue())
    
    # Create thumbnail if requested
    if create_thumb:
        thumb_io = create_thumbnail(image_file, size=thumb_size)
        thumb_filename = f"thumb_{filename}"
        
        with open(os.path.join(upload_path, thumb_filename), 'wb') as f:
            f.write(thumb_io.getvalue())
        
        return filename, thumb_filename
    
    return filename, None