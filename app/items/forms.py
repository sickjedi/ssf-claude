from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class ItemForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired()])
    item_price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)], places=2)
    submit = SubmitField('Save')
