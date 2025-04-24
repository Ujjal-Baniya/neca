"""Review forms."""
from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField, FileAllowed
from wtforms import TextAreaField, RadioField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class ReviewForm(FlaskForm):
    """Form for creating and editing reviews."""
    
    content = TextAreaField('Review', validators=[
        Optional(),
        Length(max=1000, message='Review must be less than 1000 characters')
    ])
    rating = RadioField('Rating', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please select a rating')], coerce=int)
    images = MultipleFileField('Images (Max 3)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Submit Review')