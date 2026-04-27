import pytest
from wtforms.validators import ValidationError
from app.validators import oib_validator


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
