from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


class CustomerForm(FlaskForm):
    customer_type = SelectField('Customer Type',
                                choices=[('person', 'Person'), ('company', 'Company')],
                                validators=[DataRequired()])
    # Person fields
    customer_name = StringField('Name', validators=[Optional(), Length(max=255)])
    customer_address = StringField('Address', validators=[Optional(), Length(max=255)])
    # Company fields
    company_name = StringField('Company Name', validators=[Optional(), Length(max=255)])
    company_address = StringField('Company Address', validators=[Optional(), Length(max=255)])
    company_oib = StringField('OIB', validators=[Optional(), Length(max=11)])

    submit = SubmitField('Save')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False

        ok = True
        if self.customer_type.data == 'person':
            if not self.customer_name.data:
                self.customer_name.errors.append('Name is required for a person customer.')
                ok = False
        elif self.customer_type.data == 'company':
            if not self.company_name.data:
                self.company_name.errors.append('Company name is required.')
                ok = False
            if not self.company_address.data:
                self.company_address.errors.append('Address is required.')
                ok = False
            if not self.company_oib.data:
                self.company_oib.errors.append('OIB is required.')
                ok = False

        return ok
