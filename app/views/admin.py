"""Admin views."""
from flask import redirect, url_for, request, flash
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, expose
from flask_login import current_user

from app.extensions import db
from app.models.user import User, Role, UserRole
from app.models.service import Service, ServiceCategory, ServiceImage
from app.models.review import Review, ReviewImage
from app.models.message import Message, Conversation
from app.models.notification import Notification

class SecureModelView(ModelView):
    """Base ModelView that requires admin authentication."""
    
    def is_accessible(self):
        """Check if user is admin."""
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        """Handle case when user is not admin."""
        flash('You need to be an administrator to access this page.', 'danger')
        return redirect(url_for('auth.login', next=request.url))

class SecureAdminIndexView(AdminIndexView):
    """Admin index view that requires admin authentication."""
    
    @expose('/')
    def index(self):
        """Admin dashboard page."""
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an administrator to access this page.', 'danger')
            return redirect(url_for('auth.login', next=request.url))
        
        # Get statistics for dashboard
        user_count = User.query.count()
        service_count = Service.query.count()
        review_count = Review.query.count()
        message_count = Message.query.count()
        
        # Get recent registrations
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        
        # Get recent services
        recent_services = Service.query.order_by(Service.created_at.desc()).limit(5).all()
        
        return self.render('admin/index.html',
                          user_count=user_count,
                          service_count=service_count,
                          review_count=review_count,
                          message_count=message_count,
                          recent_users=recent_users,
                          recent_services=recent_services)

class UserAdmin(SecureModelView):
    """Admin view for User model."""
    
    column_list = ('id', 'username', 'email', 'active', 'last_seen', 'created_at')
    column_searchable_list = ('username', 'email')
    column_filters = ('active', 'created_at', 'last_seen')
    column_sortable_list = ('id', 'username', 'email', 'active', 'last_seen', 'created_at')
    column_default_sort = ('created_at', True)
    
    form_columns = ('username', 'email', 'phone', 'bio', 'active')
    form_edit_rules = ('username', 'email', 'phone', 'bio', 'active')
    
    def on_model_change(self, form, model, is_created):
        """Handle model change."""
        # Don't allow admin to change their own active status
        if not is_created and model.id == current_user.id and not model.active:
            model.active = True
            flash('You cannot deactivate your own account.', 'warning')

class RoleAdmin(SecureModelView):
    """Admin view for Role model."""
    
    column_list = ('id', 'name', 'description')
    column_searchable_list = ('name', 'description')
    column_filters = ('name',)
    
    form_columns = ('name', 'description')

class UserRoleAdmin(SecureModelView):
    """Admin view for UserRole model."""
    
    column_list = ('id', 'user_id', 'role_id', 'created_at')
    column_filters = ('user_id', 'role_id')
    column_sortable_list = ('id', 'created_at')
    
    form_columns = ('user_id', 'role_id')

class ServiceAdmin(SecureModelView):
    """Admin view for Service model."""
    
    column_list = ('id', 'title', 'seller', 'price', 'price_type', 'location', 'active', 'created_at')
    column_searchable_list = ('title', 'description', 'location')
    column_filters = ('active', 'price_type', 'category', 'created_at')
    column_sortable_list = ('id', 'title', 'price', 'active', 'created_at')
    column_default_sort = ('created_at', True)
    
    form_columns = ('title', 'description', 'price', 'price_type', 'location', 'active', 'seller', 'category')

class ServiceCategoryAdmin(SecureModelView):
    """Admin view for ServiceCategory model."""
    
    column_list = ('id', 'name', 'description')
    column_searchable_list = ('name', 'description')
    column_filters = ('name',)
    
    form_columns = ('name', 'description')

class ServiceImageAdmin(SecureModelView):
    """Admin view for ServiceImage model."""
    
    column_list = ('id', 'service', 'filename', 'primary', 'created_at')
    column_filters = ('service', 'primary')
    column_sortable_list = ('id', 'created_at')
    
    form_columns = ('service', 'filename', 'original_filename', 'primary')

class ReviewAdmin(SecureModelView):
    """Admin view for Review model."""
    
    column_list = ('id', 'reviewer', 'reviewee', 'service', 'rating', 'created_at')
    column_searchable_list = ('content',)
    column_filters = ('rating', 'created_at')
    column_sortable_list = ('id', 'rating', 'created_at')
    column_default_sort = ('created_at', True)
    
    form_columns = ('content', 'rating', 'reviewer', 'reviewee', 'service')

class ReviewImageAdmin(SecureModelView):
    """Admin view for ReviewImage model."""
    
    column_list = ('id', 'review', 'filename', 'created_at')
    column_filters = ('review',)
    column_sortable_list = ('id', 'created_at')
    
    form_columns = ('review', 'filename', 'original_filename')

class MessageAdmin(SecureModelView):
    """Admin view for Message model."""
    
    column_list = ('id', 'sender', 'recipient', 'conversation', 'read', 'created_at')
    column_searchable_list = ('content',)
    column_filters = ('read', 'created_at')
    column_sortable_list = ('id', 'read', 'created_at')
    column_default_sort = ('created_at', True)
    
    form_columns = ('content', 'read', 'sender', 'recipient', 'conversation')

class ConversationAdmin(SecureModelView):
    """Admin view for Conversation model."""
    
    column_list = ('id', 'user1', 'user2', 'created_at', 'updated_at')
    column_filters = ('user1', 'user2')
    column_sortable_list = ('id', 'created_at', 'updated_at')
    column_default_sort = ('updated_at', True)
    
    form_columns = ('user1', 'user2')

class NotificationAdmin(SecureModelView):
    """Admin view for Notification model."""
    
    column_list = ('id', 'user', 'type', 'read', 'created_at')
    column_searchable_list = ('content',)
    column_filters = ('type', 'read', 'created_at')
    column_sortable_list = ('id', 'type', 'read', 'created_at')
    column_default_sort = ('created_at', True)
    
    form_columns = ('user', 'type', 'content', 'read', 'related_id')

def configure_admin_views(admin, db):
    """Configure admin views."""
    # Set admin index view
    admin.index_view = SecureAdminIndexView()
    
    # Add model views
    admin.add_view(UserAdmin(User, db.session, name='Users'))
    admin.add_view(RoleAdmin(Role, db.session, name='Roles'))
    admin.add_view(UserRoleAdmin(UserRole, db.session, name='User Roles'))
    admin.add_view(ServiceAdmin(Service, db.session, name='Services'))
    admin.add_view(ServiceCategoryAdmin(ServiceCategory, db.session, name='Categories'))
    admin.add_view(ServiceImageAdmin(ServiceImage, db.session, name='Service Images'))
    admin.add_view(ReviewAdmin(Review, db.session, name='Reviews'))
    admin.add_view(ReviewImageAdmin(ReviewImage, db.session, name='Review Images'))
    admin.add_view(MessageAdmin(Message, db.session, name='Messages'))
    admin.add_view(ConversationAdmin(Conversation, db.session, name='Conversations'))
    admin.add_view(NotificationAdmin(Notification, db.session, name='Notifications'))