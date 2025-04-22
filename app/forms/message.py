"""Message forms."""
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length

class MessageForm(FlaskForm):
    """Form for sending messages."""
    
    content = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=1, max=1000, message='Message must be between 1 and 1000 characters')
    ])
    recipient_id = HiddenField('Recipient ID', validators=[DataRequired()])
    submit = SubmitField('Send Message')