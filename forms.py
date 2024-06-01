from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField('text', validators=[DataRequired(message="You must provide text for the message!")])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired(message="You must provide a username!")])
    email = StringField('E-mail', validators=[DataRequired(message="You must provide an email!"), Email(message="You must provide a valid email!")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6,message="Your password must be at least 6 characters long!")])
    image_url = StringField('(Optional) Image URL', validators=[Optional()])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired(message="Please enter your username!")])
    password = PasswordField('Password', validators=[DataRequired(message="Please enter your password!"), Length(min=6, message="Your password must be at least 6 characters long!")])
