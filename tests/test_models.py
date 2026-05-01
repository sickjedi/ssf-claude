import pytest
from decimal import Decimal
from app import db as _db
from app.models.user import User, Role
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.organisation import Organisation
from tests.conftest import make_org


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

    def test_super_admin(self):
        assert Role.SUPER_ADMIN.label == 'Super Admin'


# ── User.can_delete / can_write / can_super_admin ─────────────────────────────

class TestUserPermissions:
    @pytest.mark.parametrize('role', [Role.SUPER_ADMIN, Role.ADMIN, Role.PRESIDENT])
    def test_can_delete_true(self, role):
        assert User(role=role).can_delete is True

    @pytest.mark.parametrize('role', [Role.VICE_PRESIDENT, Role.SECRETARY, Role.VIEWER])
    def test_can_delete_false(self, role):
        assert User(role=role).can_delete is False

    @pytest.mark.parametrize('role', [Role.SUPER_ADMIN, Role.ADMIN, Role.PRESIDENT,
                                       Role.VICE_PRESIDENT, Role.SECRETARY])
    def test_can_write_true(self, role):
        assert User(role=role).can_write is True

    def test_viewer_cannot_write(self):
        assert User(role=Role.VIEWER).can_write is False

    def test_super_admin_can_super_admin(self):
        assert User(role=Role.SUPER_ADMIN).can_super_admin is True

    @pytest.mark.parametrize('role', [Role.ADMIN, Role.PRESIDENT, Role.VIEWER])
    def test_others_cannot_super_admin(self, role):
        assert User(role=role).can_super_admin is False


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


# ── Organisation ──────────────────────────────────────────────────────────────

class TestOrganisation:
    def test_saves_and_retrieves(self, app):
        org = make_org(name='Tvornica Znanosti', oib='12345678903')
        _db.session.add(org)
        _db.session.commit()

        fetched = _db.session.get(Organisation, org.id)
        assert fetched.name == 'Tvornica Znanosti'
        assert fetched.oib == '12345678903'
        assert fetched.is_active is True

    def test_oib_must_be_unique(self, app):
        from sqlalchemy.exc import IntegrityError
        _db.session.add(make_org(oib='12345678903'))
        _db.session.commit()
        _db.session.add(make_org(name='Another Org', oib='12345678903'))
        with pytest.raises(IntegrityError):
            _db.session.commit()
        _db.session.rollback()

    def test_different_orgs_can_have_same_name(self, app):
        _db.session.add(make_org(name='Same Name', oib='12345678903'))
        _db.session.add(make_org(name='Same Name', oib='98765432109'))
        _db.session.commit()
        assert Organisation.query.filter_by(name='Same Name').count() == 2
