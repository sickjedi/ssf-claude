from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from app.validators import oib_validator


class OrganisationAdminForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=255)])
    oib = StringField('OIB', validators=[DataRequired(), Length(max=11), oib_validator])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    iban = StringField('IBAN', validators=[Optional(), Length(max=34)])
    is_active = BooleanField('Active')
    submit = SubmitField('Save')
