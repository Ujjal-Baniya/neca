"""Authentication forms."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from flask_login import current_user

from app.models.user import User
from app.extensions import db

class LoginForm(FlaskForm):
    """User login form."""
    
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    """User registration form."""
    
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=25),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must start with a letter and can only contain '
               'letters, numbers, dots or underscores')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    phone = StringField('Phone Number (Optional)', validators=[
        Length(max=15)
    ])
    is_seller = BooleanField('Register as Service Provider')
    is_consumer = BooleanField('Register as Service Consumer')
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Validate username is unique."""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Validate email is unique."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('That email address is already registered. Please use a different one.')
    
    def validate(self, **kwargs):
        """Ensure at least one role is selected."""
        if not super().validate():
            return False
        
        if not self.is_seller.data and not self.is_consumer.data:
            self.is_consumer.errors = ['You must select at least one role.']
            return False
            
        return True

class ProfileForm(FlaskForm):
    """User profile form."""
    
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=25),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must start with a letter and can only contain '
               'letters, numbers, dots or underscores')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Length(max=15)])
    bio = TextAreaField('About Me', validators=[Length(max=500)])
    profile_image = FileField('Profile Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    is_seller = BooleanField('I am a Service Provider')
    is_consumer = BooleanField('I am a Service Consumer')
    submit = SubmitField('Update Profile')
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        # Store original username and email for validation
        if current_user.is_authenticated:
            self.original_username = current_user.username
            self.original_email = current_user.email
    
    def validate_username(self, username):
        """Validate username is unique unless it's the user's current username."""
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Validate email is unique unless it's the user's current email."""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('That email address is already registered. Please use a different one.')
    
    def validate(self, **kwargs):
        """Ensure at least one role is selected."""
        if not super().validate():
            return False
        
        if not self.is_seller.data and not self.is_consumer.data:
            self.is_consumer.errors = ['You must select at least one role.']
            return False
            
        return True