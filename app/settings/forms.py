from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Optional, Length


class SettingsForm(FlaskForm):
    name = StringField('Organisation Name', validators=[Optional(), Length(max=255)])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    oib = StringField('OIB', validators=[Optional(), Length(max=11)])
    iban = StringField('IBAN / Bank Account', validators=[Optional(), Length(max=34)])
    submit = SubmitField('Save')
