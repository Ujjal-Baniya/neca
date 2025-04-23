"""Service views."""
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_, func

from app.extensions import db
from app.forms.service import ServiceForm, ServiceSearchForm
from app.models.service import Service, ServiceImage, ServiceCategory
from app.models.user import User
from app.utils.security import generate_random_filename, allowed_file

services_bp = Blueprint('services', __name__)

@services_bp.route('/')
def index():
    """List all services with search and filter capabilities."""
    form = ServiceSearchForm(request.args)
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = Service.query.filter_by(active=True)
    
    # Apply filters
    if form.query.data:
        search_term = f"%{form.query.data}%"
        query = query.filter(
            or_(
                Service.title.ilike(search_term),
                Service.description.ilike(search_term)
            )
        )
    
    if form.category_id.data and form.category_id.data != 0:
        query = query.filter(Service.category_id == form.category_id.data)
    
    if form.location.data:
        location_term = f"%{form.location.data}%"
        query = query.filter(Service.location.ilike(location_term))
    
    if form.min_price.data is not None:
        query = query.filter(Service.price >= form.min_price.data)
    
    if form.max_price.data is not None:
        query = query.filter(Service.price <= form.max_price.data)
    
    if form.min_rating.data is not None:
        # Subquery to get services with minimum rating
        from app.models.review import Review
        min_rating = form.min_rating.data
        query = query.join(Review, Service.id == Review.service_id) \
            .group_by(Service.id) \
            .having(func.avg(Review.rating) >= min_rating)
    
    if form.price_type.data != 'all':
        query = query.filter(Service.price_type == form.price_type.data)
    
    # Apply sorting
    if form.sort.data == 'newest':
        query = query.order_by(Service.created_at.desc())
    elif form.sort.data == 'oldest':
        query = query.order_by(Service.created_at.asc())
    elif form.sort.data == 'price_low':
        query = query.order_by(Service.price.asc())
    elif form.sort.data == 'price_high':
        query = query.order_by(Service.price.desc())
    elif form.sort.data == 'rating':
        # Sort by average rating
        from app.models.review import Review
        subquery = db.session.query(
            Review.service_id,
            func.avg(Review.rating).label('avg_rating')
        ).group_by(Review.service_id).subquery()
        
        query = query.outerjoin(
            subquery, Service.id == subquery.c.service_id
        ).order_by(subquery.c.avg_rating.desc().nullslast())
    
    # Paginate results
    services = query.paginate(page=page, per_page=current_app.config['SERVICES_PER_PAGE'])
    
    # Get categories for filter dropdown
    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()
    
    return render_template('services/index.html',
                          services=services,
                          form=form,
                          categories=categories)

@services_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new service."""
    if not current_user.is_seller:
        flash('You must be registered as a service provider to create services.', 'warning')
        return redirect(url_for('auth.profile'))
    
    form = ServiceForm()
    
    if form.validate_on_submit():
        service = Service(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            price_type=form.price_type.data,
            location=form.location.data,
            category_id=form.category_id.data if form.category_id.data != 0 else None,
            active=form.active.data,
            seller_id=current_user.id
        )
        
        db.session.add(service)
        db.session.commit()
        
        # Handle image uploads
        if form.images.data:
            upload_success = _save_service_images(service.id, form.images.data)
            if not upload_success:
                flash('Some images could not be uploaded.', 'warning')
        
        flash('Your service has been created!', 'success')
        return redirect(url_for('services.view', service_id=service.id))
    
    return render_template('services/create.html', form=form)

@services_bp.route('/<int:service_id>')
def view(service_id):
    """View a single service."""
    service = Service.query.get_or_404(service_id)
    
    if not service.active and (not current_user.is_authenticated or service.seller_id != current_user.id):
        abort(404)
    
    # Get reviews for this service
    page = request.args.get('page', 1, type=int)
    reviews = service.reviews.order_by(db.text('created_at DESC')).paginate(
        page=page, per_page=current_app.config['REVIEWS_PER_PAGE']
    )
    
    # Check if current user has saved this service
    has_saved = False
    if current_user.is_authenticated:
        has_saved = current_user.has_saved_service(service)
    
    return render_template('services/view.html',
                          service=service,
                          reviews=reviews,
                          has_saved=has_saved)

@services_bp.route('/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(service_id):
    """Edit a service."""
    service = Service.query.get_or_404(service_id)
    
    # Ensure user owns the service
    if service.seller_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    form = ServiceForm(obj=service)
    
    if form.validate_on_submit():
        service.title = form.title.data
        service.description = form.description.data
        service.price = form.price.data
        service.price_type = form.price_type.data
        service.location = form.location.data
        service.category_id = form.category_id.data if form.category_id.data != 0 else None
        service.active = form.active.data
        
        # Handle image uploads
        if form.images.data and any(image.filename for image in form.images.data):
            upload_success = _save_service_images(service.id, form.images.data)
            if not upload_success:
                flash('Some images could not be uploaded.', 'warning')
        
        db.session.commit()
        flash('Your service has been updated!', 'success')
        return redirect(url_for('services.view', service_id=service.id))
    
    return render_template('services/edit.html', form=form, service=service)

@services_bp.route('/<int:service_id>/delete', methods=['POST'])
@login_required
def delete(service_id):
    """Delete a service."""
    service = Service.query.get_or_404(service_id)
    
    # Ensure user owns the service
    if service.seller_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Delete service images
    for image in service.images:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'services', image.filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(service)
    db.session.commit()
    
    flash('Your service has been deleted.', 'success')
    return redirect(url_for('services.index'))

@services_bp.route('/<int:service_id>/save', methods=['POST'])
@login_required
def save(service_id):
    """Save a service to user's favorites."""
    service = Service.query.get_or_404(service_id)
    
    if current_user.has_saved_service(service):
        flash('You have already saved this service.', 'info')
    else:
        current_user.save_service(service)
        flash('Service saved to your favorites.', 'success')
    
    return redirect(url_for('services.view', service_id=service_id))

@services_bp.route('/<int:service_id>/unsave', methods=['POST'])
@login_required
def unsave(service_id):
    """Remove a service from user's favorites."""
    service = Service.query.get_or_404(service_id)
    
    if current_user.has_saved_service(service):
        current_user.unsave_service(service)
        flash('Service removed from your favorites.', 'success')
    else:
        flash('This service was not in your favorites.', 'info')
    
    return redirect(url_for('services.view', service_id=service_id))

@services_bp.route('/<int:service_id>/images/<int:image_id>/delete', methods=['POST'])
@login_required
def delete_image(service_id, image_id):
    """Delete a service image."""
    service = Service.query.get_or_404(service_id)
    image = ServiceImage.query.get_or_404(image_id)
    
    # Ensure user owns the service and image
    if service.seller_id != current_user.id or image.service_id != service_id:
        abort(403)
    
    # Delete image file
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'services', image.filename)
    if os.path.exists(image_path):
        os.remove(image_path)
    
    db.session.delete(image)
    db.session.commit()
    
    flash('Image has been deleted.', 'success')
    return redirect(url_for('services.edit', service_id=service_id))

@services_bp.route('/<int:service_id>/images/<int:image_id>/set-primary', methods=['GET', 'POST'])
@login_required
def set_primary_image(service_id, image_id):
    """Set an image as the primary image for a service."""
    service = Service.query.get_or_404(service_id)
    image = ServiceImage.query.get_or_404(image_id)
    
    # Ensure user owns the service and image
    if service.seller_id != current_user.id or image.service_id != service_id:
        abort(403)
    
    # Set this image as primary and others as non-primary
    for img in service.images:
        img.primary = (img.id == image_id)
    
    db.session.commit()
    
    flash('Primary image has been updated.', 'success')
    return redirect(url_for('services.edit', service_id=service_id))

@services_bp.route('/by-seller/<int:seller_id>')
def by_seller(seller_id):
    """View all services by a specific seller."""
    seller = User.query.get_or_404(seller_id)
    
    if not seller.is_seller:
        abort(404)
    
    page = request.args.get('page', 1, type=int)
    services = Service.query.filter_by(seller_id=seller_id, active=True) \
        .order_by(Service.created_at.desc()) \
        .paginate(page=page, per_page=current_app.config['SERVICES_PER_PAGE'])
    
    return render_template('services/by_seller.html',
                          services=services,
                          seller=seller)

@services_bp.route('/saved')
@login_required
def saved():
    """View user's saved services."""
    page = request.args.get('page', 1, type=int)
    
    # Get user's saved services
    saved_services = current_user.saved_services_rel
    
    # Create a paginated list
    from app.utils.pagination import create_paginated_list
    paginated = create_paginated_list(saved_services, page, current_app.config['SERVICES_PER_PAGE'])
    
    return render_template('services/saved.html', services=paginated)

def _save_service_images(service_id, images):
    """Save service images to disk and database."""
    success = True
    primary_set = False
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'services')
    
    # Limit to 5 images
    images = [img for img in images if img and img.filename.strip()][:5]
    
    for image in images:
        if not allowed_file(image.filename):
            success = False
            continue
        
        try:
            # Generate secure filename
            filename = secure_filename(image.filename)
            random_filename = generate_random_filename(filename)
            
            # Save the image
            image_path = os.path.join(upload_folder, random_filename)
            image.save(image_path)
            
            # Create database record
            service_image = ServiceImage(
                filename=random_filename,
                original_filename=filename,
                service_id=service_id,
                primary=not primary_set  # First image becomes primary
            )
            
            db.session.add(service_image)
            primary_set = True
        except Exception as e:
            current_app.logger.error(f"Error saving service image: {e}")
            success = False
    
    db.session.commit()
    return success