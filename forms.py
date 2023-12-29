from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, URL, Length


class RegisterForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()])
    email = EmailField("Email:", validators=[DataRequired(), Email()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = EmailField("Email:", validators=[DataRequired(), Email()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Submit")


class AddForm(FlaskForm):
    name = StringField("Name:", validators=[DataRequired()])
    map_url = StringField("Map URL:", validators=[DataRequired(), URL()])
    img_url = StringField("Image URL:", validators=[DataRequired(), URL()])
    location = StringField("Location:", validators=[DataRequired()])
    coffee_price = StringField("Coffee Price:", validators=[DataRequired()])
    seats = StringField("Number of seats:", validators=[DataRequired()])
    sockets = BooleanField("Does the cafe have sockets?")
    toilet = BooleanField("Does the cafe have toilets?")
    wifi = BooleanField("Does the cafe have wifi?")
    call = BooleanField("Does the cafe offer call services?")
    submit = SubmitField("Submit")


class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email:", validators=[DataRequired(), Email()])
    submit = SubmitField("Submit")


class RecoveryCodeForm(FlaskForm):
    pin = StringField("Pin:", validators=[DataRequired(), Length(max=3, min=3)])
    submit = SubmitField("Submit")


class ChangePasswordForm(FlaskForm):
    password = PasswordField("New Password:", validators=[DataRequired()])
    submit = SubmitField("Submit")


def searchform(inplace_value):
    class SearchForm(FlaskForm):
        search = StringField("", render_kw={'value': inplace_value})
        submit = SubmitField("Search Cafe")
    return SearchForm
