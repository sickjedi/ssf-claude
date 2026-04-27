import pytest
from decimal import Decimal
from unittest.mock import patch
from app.invoices.routes import _parse_items, _generate_invoice_number


# ── _parse_items ──────────────────────────────────────────────────────────────

class TestParseItems:
    def _post(self, app, data):
        return app.test_request_context('/', method='POST', data=data)

    def test_parses_custom_and_catalog_items(self, app):
        with self._post(app, {
            'item_id[]': ['', '1'],
            'item_name[]': ['Custom Item', 'Catalog Item'],
            'item_price[]': ['10.00', '25.50'],
            'item_quantity[]': ['2', '1'],
        }):
            result = _parse_items()

        assert len(result) == 2
        assert result[0] == {
            'item_id': None,
            'item_name': 'Custom Item',
            'item_price': Decimal('10.00'),
            'item_quantity': 2,
        }
        assert result[1] == {
            'item_id': 1,
            'item_name': 'Catalog Item',
            'item_price': Decimal('25.50'),
            'item_quantity': 1,
        }

    def test_price_is_decimal_not_float(self, app):
        with self._post(app, {
            'item_id[]': [''],
            'item_name[]': ['Item'],
            'item_price[]': ['9.99'],
            'item_quantity[]': ['1'],
        }):
            result = _parse_items()
        assert isinstance(result[0]['item_price'], Decimal)

    def test_skips_blank_name_rows(self, app):
        with self._post(app, {
            'item_id[]': ['', ''],
            'item_name[]': ['Real Item', ''],
            'item_price[]': ['5.00', '10.00'],
            'item_quantity[]': ['1', '1'],
        }):
            result = _parse_items()
        assert len(result) == 1
        assert result[0]['item_name'] == 'Real Item'

    def test_strips_whitespace_from_name(self, app):
        with self._post(app, {
            'item_id[]': [''],
            'item_name[]': ['  Padded  '],
            'item_price[]': ['1.00'],
            'item_quantity[]': ['1'],
        }):
            result = _parse_items()
        assert result[0]['item_name'] == 'Padded'

    def test_empty_arrays_return_empty_list(self, app):
        with self._post(app, {
            'item_id[]': [],
            'item_name[]': [],
            'item_price[]': [],
            'item_quantity[]': [],
        }):
            result = _parse_items()
        assert result == []

    def test_mismatched_array_lengths_returns_none(self, app):
        with self._post(app, {
            'item_id[]': ['', ''],
            'item_name[]': ['Only One Name'],
            'item_price[]': ['5.00', '10.00'],
            'item_quantity[]': ['1', '2'],
        }):
            result = _parse_items()
        assert result is None

    def test_invalid_price_skipped(self, app):
        with self._post(app, {
            'item_id[]': [''],
            'item_name[]': ['Bad Item'],
            'item_price[]': ['not-a-price'],
            'item_quantity[]': ['1'],
        }):
            result = _parse_items()
        assert result == []

    def test_all_blank_names_return_empty_list(self, app):
        with self._post(app, {
            'item_id[]': ['', ''],
            'item_name[]': ['', '   '],
            'item_price[]': ['5.00', '10.00'],
            'item_quantity[]': ['1', '1'],
        }):
            result = _parse_items()
        assert result == []


# ── _generate_invoice_number ──────────────────────────────────────────────────

def _mock_db_max(return_value):
    """Patch db.session.query(...).filter(...).scalar() to return a fixed value."""
    mock = patch('app.invoices.routes.db')
    m = mock.start()
    m.session.query.return_value.filter.return_value.scalar.return_value = return_value
    return mock


class TestGenerateInvoiceNumber:
    def test_first_invoice_of_year(self, app):
        with patch('app.invoices.routes.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.scalar.return_value = None
            assert _generate_invoice_number(2026) == '01/2026'

    def test_increments_from_existing_max(self, app):
        with patch('app.invoices.routes.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.scalar.return_value = 5
            assert _generate_invoice_number(2026) == '06/2026'

    def test_zero_max_treated_as_no_invoices(self, app):
        with patch('app.invoices.routes.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
            assert _generate_invoice_number(2026) == '01/2026'

    def test_uses_provided_year(self, app):
        with patch('app.invoices.routes.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.scalar.return_value = None
            assert _generate_invoice_number(2025) == '01/2025'

    def test_sequence_beyond_two_digits(self, app):
        with patch('app.invoices.routes.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.scalar.return_value = 99
            assert _generate_invoice_number(2026) == '100/2026'
