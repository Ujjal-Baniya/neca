"""Review views."""
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms.review import ReviewForm
from app.models.review import Review, ReviewImage
from app.models.service import Service
from app.models.user import User
from app.models.notification import Notification
from app.utils.security import generate_random_filename, allowed_file

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/create/<int:service_id>', methods=['GET', 'POST'])
@login_required
def create(service_id):
    """Create a new review for a service."""
    service = Service.query.get_or_404(service_id)
    
    # Check if user has already reviewed this service
    existing_review = Review.query.filter_by(
        reviewer_id=current_user.id,
        service_id=service_id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this service.', 'info')
        return redirect(url_for('reviews.edit', review_id=existing_review.id))
    
    # Ensure user is not reviewing their own service
    if service.seller_id == current_user.id:
        flash('You cannot review your own service.', 'warning')
        return redirect(url_for('services.view', service_id=service_id))
    
    form = ReviewForm()
    
    if form.validate_on_submit():
        review = Review(
            content=form.content.data,
            rating=form.rating.data,
            reviewer_id=current_user.id,
            reviewee_id=service.seller_id,
            service_id=service_id
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Handle image uploads
        if form.images.data:
            upload_success = _save_review_images(review.id, form.images.data)
            if not upload_success:
                flash('Some images could not be uploaded.', 'warning')
        
        # Create notification for service owner
        notification_content = f"{current_user.username} left a review for your service \"{service.title}\""
        Notification.create(
            user_id=service.seller_id,
            type='review',
            content=notification_content,
            related_id=review.id
        )
        
        flash('Your review has been posted!', 'success')
        return redirect(url_for('services.view', service_id=service_id))
    
    return render_template('reviews/create.html', form=form, service=service)

@reviews_bp.route('/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit(review_id):
    """Edit an existing review."""
    review = Review.query.get_or_404(review_id)
    
    # Ensure user is the review owner
    if review.reviewer_id != current_user.id:
        abort(403)
    
    form = ReviewForm(obj=review)
    
    if form.validate_on_submit():
        review.content = form.content.data
        review.rating = form.rating.data
        
        # Handle image uploads
        if form.images.data and any(image.filename for image in form.images.data):
            upload_success = _save_review_images(review.id, form.images.data)
            if not upload_success:
                flash('Some images could not be uploaded.', 'warning')
        
        db.session.commit()
        flash('Your review has been updated!', 'success')
        
        if review.service_id:
            return redirect(url_for('services.view', service_id=review.service_id))
        else:
            return redirect(url_for('profiles.view', user_id=review.reviewee_id))
    
    return render_template('reviews/edit.html', form=form, review=review)

@reviews_bp.route('/delete/<int:review_id>', methods=['POST'])
@login_required
def delete(review_id):
    """Delete a review."""
    review = Review.query.get_or_404(review_id)
    
    # Ensure user is the review owner or an admin
    if review.reviewer_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Get the redirect target before deleting
    service_id = review.service_id
    reviewee_id = review.reviewee_id
    
    # Delete review images
    for image in review.images:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reviews', image.filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(review)
    db.session.commit()
    
    flash('Your review has been deleted.', 'success')
    
    if service_id:
        return redirect(url_for('services.view', service_id=service_id))
    else:
        return redirect(url_for('profiles.view', user_id=reviewee_id))

@reviews_bp.route('/user/<int:user_id>/create', methods=['GET', 'POST'])
@login_required
def create_user_review(user_id):
    """Create a new review for a user."""
    user = User.query.get_or_404(user_id)
    
    # Check if user has already reviewed this user
    existing_review = Review.query.filter_by(
        reviewer_id=current_user.id,
        reviewee_id=user_id,
        service_id=None
    ).first()
    
    if existing_review:
        flash('You have already reviewed this user.', 'info')
        return redirect(url_for('reviews.edit', review_id=existing_review.id))
    
    # Ensure user is not reviewing themselves
    if user_id == current_user.id:
        flash('You cannot review yourself.', 'warning')
        return redirect(url_for('profiles.view', user_id=user_id))
    
    form = ReviewForm()
    
    if form.validate_on_submit():
        review = Review(
            content=form.content.data,
            rating=form.rating.data,
            reviewer_id=current_user.id,
            reviewee_id=user_id,
            service_id=None  # This is a user review, not a service review
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Handle image uploads
        if form.images.data:
            upload_success = _save_review_images(review.id, form.images.data)
            if not upload_success:
                flash('Some images could not be uploaded.', 'warning')
        
        # Create notification for user being reviewed
        notification_content = f"{current_user.username} left you a review"
        Notification.create(
            user_id=user_id,
            type='review',
            content=notification_content,
            related_id=review.id
        )
        
        flash('Your review has been posted!', 'success')
        return redirect(url_for('profiles.view', user_id=user_id))
    
    return render_template('reviews/create_user.html', form=form, user=user)

@reviews_bp.route('/<int:review_id>/images/<int:image_id>/delete', methods=['POST'])
@login_required
def delete_image(review_id, image_id):
    """Delete a review image."""
    review = Review.query.get_or_404(review_id)
    image = ReviewImage.query.get_or_404(image_id)
    
    # Ensure user owns the review and image
    if review.reviewer_id != current_user.id or image.review_id != review_id:
        abort(403)
    
    # Delete image file
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reviews', image.filename)
    if os.path.exists(image_path):
        os.remove(image_path)
    
    db.session.delete(image)
    db.session.commit()
    
    flash('Image has been deleted.', 'success')
    return redirect(url_for('reviews.edit', review_id=review_id))

@reviews_bp.route('/by-user/<int:user_id>')
def by_user(user_id):
    """View all reviews by a specific user."""
    user = User.query.get_or_404(user_id)
    
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.filter_by(reviewer_id=user_id) \
        .order_by(Review.created_at.desc()) \
        .paginate(page=page, per_page=current_app.config['REVIEWS_PER_PAGE'])
    
    return render_template('reviews/by_user.html',
                          reviews=reviews,
                          user=user)

@reviews_bp.route('/for-user/<int:user_id>')
def for_user(user_id):
    """View all reviews for a specific user."""
    user = User.query.get_or_404(user_id)
    
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.filter_by(reviewee_id=user_id) \
        .order_by(Review.created_at.desc()) \
        .paginate(page=page, per_page=current_app.config['REVIEWS_PER_PAGE'])
    
    return render_template('reviews/for_user.html',
                          reviews=reviews,
                          user=user)

def _save_review_images(review_id, images):
    """Save review images to disk and database."""
    success = True
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reviews')
    
    # Limit to 3 images
    images = [img for img in images if img and img.filename.strip()][:3]
    
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
            review_image = ReviewImage(
                filename=random_filename,
                original_filename=filename,
                review_id=review_id
            )
            
            db.session.add(review_image)
        except Exception as e:
            current_app.logger.error(f"Error saving review image: {e}")
            success = False
    
    db.session.commit()
    return success