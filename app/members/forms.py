from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


class MemberForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    oib = StringField('OIB', validators=[DataRequired(), Length(min=11, max=11)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired(), Length(max=255)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=50)])
    email_address = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    gdpr = BooleanField('GDPR Consent', validators=[DataRequired(message='GDPR consent is required.')])
    is_active = BooleanField('Active')
    end_date = DateField('End Date', validators=[Optional()])
    end_reason = TextAreaField('End Reason', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save')
