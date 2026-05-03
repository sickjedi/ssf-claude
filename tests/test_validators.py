import pytest
from wtforms.validators import ValidationError
from app.validators import oib_validator, check_password_strength, password_validator


class _Field:
    def __init__(self, data):
        self.data = data


class _Form:
    pass


VALID_OIBS = [
    '12345678903',
    '00000000001',
    '11111111119',
]

INVALID_CHECKSUM_OIBS = [
    '12345678900',  # correct check digit is 3
    '00000000009',  # correct check digit is 1
    '11111111110',  # correct check digit is 9
]


@pytest.mark.parametrize('oib', VALID_OIBS)
def test_valid_oib_passes(oib):
    oib_validator(_Form(), _Field(oib))


@pytest.mark.parametrize('oib', INVALID_CHECKSUM_OIBS)
def test_invalid_checksum_raises(oib):
    with pytest.raises(ValidationError, match='not valid'):
        oib_validator(_Form(), _Field(oib))


def test_too_short_raises():
    with pytest.raises(ValidationError, match='11 digits'):
        oib_validator(_Form(), _Field('123456'))


def test_too_long_raises():
    with pytest.raises(ValidationError, match='11 digits'):
        oib_validator(_Form(), _Field('123456789012'))


def test_non_digits_raises():
    with pytest.raises(ValidationError, match='11 digits'):
        oib_validator(_Form(), _Field('1234567890A'))


def test_empty_string_passes():
    oib_validator(_Form(), _Field(''))


def test_none_passes():
    oib_validator(_Form(), _Field(None))


def test_whitespace_only_passes():
    oib_validator(_Form(), _Field('   '))


# ── check_password_strength ──────────────────────────────────────────────────

class TestCheckPasswordStrength:
    def test_valid_password_returns_none(self):
        assert check_password_strength('SecureP@ss12') is None

    def test_too_short_fails(self):
        assert check_password_strength('Short1@A') is not None

    def test_exactly_11_chars_fails(self):
        assert check_password_strength('SecureP@ss1') is not None

    def test_exactly_12_chars_passes(self):
        assert check_password_strength('SecureP@ss12') is None

    def test_no_uppercase_fails(self):
        assert check_password_strength('securep@ss12') is not None

    def test_no_lowercase_fails(self):
        assert check_password_strength('SECUREP@SS12') is not None

    def test_no_digit_fails(self):
        assert check_password_strength('SecureP@sswd') is not None

    def test_no_special_char_fails(self):
        assert check_password_strength('SecurePass12') is not None

    def test_empty_string_fails(self):
        assert check_password_strength('') is not None

    def test_none_fails(self):
        assert check_password_strength(None) is not None

    def test_error_message_is_string(self):
        assert isinstance(check_password_strength('short'), str)


class TestPasswordValidator:
    def test_valid_password_does_not_raise(self):
        password_validator(_Form(), _Field('SecureP@ss12'))

    def test_weak_password_raises_validation_error(self):
        with pytest.raises(ValidationError):
            password_validator(_Form(), _Field('short'))

    def test_missing_special_char_raises(self):
        with pytest.raises(ValidationError):
            password_validator(_Form(), _Field('SecurePass12'))

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError):
            password_validator(_Form(), _Field(''))

    def test_none_field_data_raises(self):
        with pytest.raises(ValidationError):
            password_validator(_Form(), _Field(None))
