from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired

class EnterTimeForm(FlaskForm):
    time = StringField('', render_kw={'class': 'time-input', 'autofocus': True})

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()], render_kw={'class': 'form-input'})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={'class': 'form-input'})
    submit = SubmitField("Sign Up!", render_kw={'class': 'sign-up'})

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()], render_kw={'class': 'form-input'})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={'class': 'form-input'})
    submit = SubmitField("Welcome Back!", render_kw={'class': 'sign-up'})

class DropdownForm(FlaskForm):
    mode = SelectField('', choices = ("Timer", "Input"), render_kw={"style": "margin-left: 20px", "id": "dropdown-form", "onchange": "this.form.submit()"})