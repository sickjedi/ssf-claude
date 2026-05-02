from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Email
from app.validators import oib_validator


class OrganisationAdminForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=255)])
    oib = StringField('OIB', validators=[DataRequired(), Length(max=11), oib_validator])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    iban = StringField('IBAN', validators=[Optional(), Length(max=34)])
    is_active = BooleanField('Active')

    add_first_member = BooleanField('Add First Member (President)')
    member_first_name = StringField('First Name', validators=[Optional(), Length(max=100)])
    member_last_name = StringField('Last Name', validators=[Optional(), Length(max=100)])
    member_oib = StringField('OIB', validators=[Optional(), Length(max=11), oib_validator])
    member_date_of_birth = DateField('Date of Birth', validators=[Optional()])
    member_address = StringField('Address', validators=[Optional(), Length(max=255)])
    member_phone = StringField('Phone', validators=[Optional(), Length(max=50)])
    member_email = StringField('Email', validators=[Optional(), Email(), Length(max=255)])
    user_login_email = StringField('Login Email', validators=[Optional(), Email(), Length(max=255)])
    user_password = PasswordField('Password', validators=[Optional(), Length(min=8, max=128)])

    submit = SubmitField('Save')


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')
