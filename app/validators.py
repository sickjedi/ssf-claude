import re
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


def check_password_strength(password: str | None) -> str | None:
    if not password or len(password) < 12:
        return 'Password must be at least 12 characters.'
    if not any(c.isupper() for c in password):
        return 'Password must contain at least one uppercase letter.'
    if not any(c.islower() for c in password):
        return 'Password must contain at least one lowercase letter.'
    if not any(c.isdigit() for c in password):
        return 'Password must contain at least one number.'
    if not re.search(r'[^a-zA-Z0-9\s]', password):
        return 'Password must contain at least one special character.'
    return None


def password_validator(form, field):
    error = check_password_strength(field.data)
    if error:
        raise ValidationError(error)
