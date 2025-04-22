"""Service forms."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, TextAreaField, FloatField, SelectField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.models.service import ServiceCategory

class ServiceForm(FlaskForm):
    """Form for creating and editing services."""
    
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=5, max=255, message='Title must be between 5 and 255 characters')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=20, message='Description must be at least 20 characters')
    ])
    price = FloatField('Price', validators=[
        DataRequired(),
        NumberRange(min=0, message='Price must be a positive number')
    ])
    price_type = SelectField('Price Type', choices=[
        ('hourly', 'Per Hour'),
        ('fixed', 'Fixed Price')
    ], validators=[DataRequired()])
    location = StringField('Location', validators=[
        DataRequired(),
        Length(min=3, max=255, message='Location must be between 3 and 255 characters')
    ])
    category_id = SelectField('Category', coerce=int, validators=[
        DataRequired(message='Please select a category')
    ])
    images = MultipleFileField('Images (Max 5)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    active = BooleanField('Active', default=True)
    submit = SubmitField('Save Service')
    
    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        # Dynamically load categories
        self.category_id.choices = [(c.id, c.name) for c in ServiceCategory.query.order_by('name').all()]
        # Add empty choice
        self.category_id.choices.insert(0, (0, 'Select Category'))
    
    def validate_category_id(self, field):
        """Validate category selection."""
        if field.data == 0:
            raise ValueError('Please select a valid category')

class ServiceSearchForm(FlaskForm):
    """Form for searching services."""
    
    query = StringField('Search', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    min_price = FloatField('Min Price', validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField('Max Price', validators=[Optional(), NumberRange(min=0)])
    min_rating = IntegerField('Min Rating', validators=[Optional(), NumberRange(min=1, max=5)])
    sort = SelectField('Sort By', choices=[
        ('newest', 'Newest'),
        ('oldest', 'Oldest'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low'),
        ('rating', 'Highest Rating')
    ], default='newest')
    price_type = SelectField('Price Type', choices=[
        ('all', 'All'),
        ('hourly', 'Hourly'),
        ('fixed', 'Fixed Price')
    ], default='all')
    submit = SubmitField('Search')
    
    def __init__(self, *args, **kwargs):
        super(ServiceSearchForm, self).__init__(*args, **kwargs)
        # Dynamically load categories
        categories = ServiceCategory.query.order_by('name').all()
        self.category_id.choices = [(0, 'All Categories')]
        self.category_id.choices.extend([(c.id, c.name) for c in categories])