from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, DateField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional
from app.models.user import Role
from app.validators import oib_validator


class MemberForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    oib = StringField('OIB', validators=[DataRequired(), oib_validator])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired(), Length(max=255)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=50)])
    email_address = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    gdpr = BooleanField('GDPR Consent', validators=[DataRequired(message='GDPR consent is required.')])
    is_active = BooleanField('Active', default=True)
    end_date = DateField('End Date', validators=[Optional()])
    end_reason = TextAreaField('End Reason', validators=[Optional(), Length(max=500)])
    # Existing user account — rendered when member already has a user
    user_role = SelectField('Role', choices=[(r.value, r.label) for r in Role], validators=[Optional()])
    user_is_active = BooleanField('User Account Active')
    # New user account — rendered when member has no user
    new_user_email = StringField('Email', validators=[Optional(), Email(), Length(max=255)])
    new_user_password = StringField('Password', validators=[Optional(), Length(min=8, max=128)])
    new_user_role = SelectField('Role', choices=[(r.value, r.label) for r in Role], validators=[Optional()])
    submit = SubmitField('Save')
