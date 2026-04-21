from wtforms.validators import ValidationError


def oib_validator(form, field):
    oib = (field.data or '').strip()
    if not oib:
        return
    if len(oib) != 11 or not oib.isdigit():
        raise ValidationError('OIB must be exactly 11 digits.')
    remainder = 10
    for digit in oib[:10]:
        remainder = (remainder + int(digit)) % 10
        if remainder == 0:
            remainder = 10
        remainder = (remainder * 2) % 11
    check = 11 - remainder
    if check == 10:
        check = 0
    if check != int(oib[10]):
        raise ValidationError('OIB is not valid.')
