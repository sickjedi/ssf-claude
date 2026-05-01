from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from app.validators import oib_validator


class OrganisationForm(FlaskForm):
    name = StringField('Organisation Name', validators=[DataRequired(), Length(max=255)])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    oib = StringField('OIB', validators=[DataRequired(), Length(max=11), oib_validator])
    iban = StringField('IBAN / Bank Account', validators=[Optional(), Length(max=34)])
    submit = SubmitField('Save')
