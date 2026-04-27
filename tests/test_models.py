import pytest
from decimal import Decimal
from app import db as _db
from app.models.user import User, Role
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.settings import Settings


# ── Role.label ────────────────────────────────────────────────────────────────

class TestRoleLabel:
    def test_admin(self):
        assert Role.ADMIN.label == 'Admin'

    def test_president(self):
        assert Role.PRESIDENT.label == 'President'

    def test_vice_president(self):
        assert Role.VICE_PRESIDENT.label == 'Vice President'

    def test_secretary(self):
        assert Role.SECRETARY.label == 'Secretary'

    def test_viewer(self):
        assert Role.VIEWER.label == 'Viewer'


# ── User.can_delete / can_write ───────────────────────────────────────────────

class TestUserPermissions:
    @pytest.mark.parametrize('role', [Role.ADMIN, Role.PRESIDENT])
    def test_can_delete_true(self, role):
        assert User(role=role).can_delete is True

    @pytest.mark.parametrize('role', [Role.VICE_PRESIDENT, Role.SECRETARY, Role.VIEWER])
    def test_can_delete_false(self, role):
        assert User(role=role).can_delete is False

    @pytest.mark.parametrize('role', [Role.ADMIN, Role.PRESIDENT, Role.VICE_PRESIDENT, Role.SECRETARY])
    def test_can_write_true(self, role):
        assert User(role=role).can_write is True

    def test_viewer_cannot_write(self):
        assert User(role=Role.VIEWER).can_write is False


# ── InvoiceItem.subtotal ──────────────────────────────────────────────────────

class TestInvoiceItemSubtotal:
    def test_whole_numbers(self):
        item = InvoiceItem(item_price=Decimal('10.00'), item_quantity=3)
        assert item.subtotal == Decimal('30.00')

    def test_fractional_price(self):
        item = InvoiceItem(item_price=Decimal('9.99'), item_quantity=2)
        assert item.subtotal == Decimal('19.98')

    def test_quantity_one(self):
        item = InvoiceItem(item_price=Decimal('42.50'), item_quantity=1)
        assert item.subtotal == Decimal('42.50')


# ── Invoice.total ─────────────────────────────────────────────────────────────

class TestInvoiceTotal:
    def test_sums_multiple_items(self):
        invoice = Invoice()
        invoice.items = [
            InvoiceItem(item_price=Decimal('10.00'), item_quantity=2),
            InvoiceItem(item_price=Decimal('5.00'), item_quantity=3),
        ]
        assert invoice.total == Decimal('35.00')

    def test_empty_invoice_totals_zero(self):
        invoice = Invoice()
        invoice.items = []
        assert invoice.total == 0

    def test_single_item(self):
        invoice = Invoice()
        invoice.items = [InvoiceItem(item_price=Decimal('100.00'), item_quantity=1)]
        assert invoice.total == Decimal('100.00')


# ── Settings.get ──────────────────────────────────────────────────────────────

class TestSettingsGet:
    def test_returns_transient_instance_when_table_empty(self):
        s = Settings.get()
        assert s.id is None

    def test_does_not_persist_on_read(self):
        Settings.get()
        assert Settings.query.count() == 0

    def test_returns_existing_row(self):
        saved = Settings(name='Test Org')
        _db.session.add(saved)
        _db.session.commit()

        result = Settings.get()
        assert result.id == saved.id
        assert result.name == 'Test Org'
