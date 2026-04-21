from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SubmitField
from wtforms.validators import DataRequired


class InvoiceForm(FlaskForm):
    invoice_date = DateField('Invoice Date', validators=[DataRequired()])
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')
