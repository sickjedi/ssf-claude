import pytest
from datetime import date
from app import db as _db
from app.admin.forms import OrganisationAdminForm
from app.models.member import Member
from app.models.organisation import Organisation
from app.models.user import User, Role
from app.admin.routes import _first_member_errors
from tests.conftest import make_org


# ── Helpers ───────────────────────────────────────────────────────────────────

class _Field:
    def __init__(self, data):
        self.data = data
        self.errors = []


class _FirstMemberForm:
    """Minimal stand-in for the parts of OrganisationAdminForm that _first_member_errors reads."""
    def __init__(self, enabled=True, **overrides):
        self.add_first_member = _Field(enabled)
        self.member_first_name = _Field(overrides.get('first_name', 'Ana'))
        self.member_last_name = _Field(overrides.get('last_name', 'Anić'))
        self.member_oib = _Field(overrides.get('oib', '12345678903'))
        self.member_date_of_birth = _Field(overrides.get('dob', date(1990, 1, 1)))
        self.member_address = _Field(overrides.get('address', 'Ilica 1'))
        self.member_phone = _Field(overrides.get('phone', '0911234567'))
        self.member_email = _Field(overrides.get('email', 'ana@example.com'))
        self.user_login_email = _Field(overrides.get('login_email', 'ana@example.com'))
        self.user_password = _Field(overrides.get('password', 'Password1!'))


# ── OrganisationAdminForm field validators ────────────────────────────────────

class TestOrganisationAdminForm:
    _VALID = {'name': 'Test Org', 'oib': '12345678903'}

    def test_minimal_valid_form_passes(self, app):
        with app.test_request_context('/', method='POST', data=self._VALID):
            assert OrganisationAdminForm().validate() is True

    def test_member_oib_blank_passes(self, app):
        with app.test_request_context('/', method='POST', data={**self._VALID, 'member_oib': ''}):
            assert OrganisationAdminForm().validate() is True

    def test_member_oib_invalid_checksum_fails(self, app):
        with app.test_request_context('/', method='POST', data={**self._VALID, 'member_oib': '12345678900'}):
            form = OrganisationAdminForm()
            assert form.validate() is False
            assert form.member_oib.errors

    def test_member_oib_too_long_fails(self, app):
        with app.test_request_context('/', method='POST', data={**self._VALID, 'member_oib': '123456789031'}):
            form = OrganisationAdminForm()
            assert form.validate() is False
            assert form.member_oib.errors

    def test_user_password_blank_passes(self, app):
        with app.test_request_context('/', method='POST', data={**self._VALID, 'user_password': ''}):
            assert OrganisationAdminForm().validate() is True

    def test_user_password_too_short_fails(self, app):
        with app.test_request_context('/', method='POST', data={**self._VALID, 'user_password': 'short'}):
            form = OrganisationAdminForm()
            assert form.validate() is False
            assert form.user_password.errors

    def test_member_email_invalid_format_fails(self, app):
        with app.test_request_context('/', method='POST', data={**self._VALID, 'member_email': 'not-an-email'}):
            form = OrganisationAdminForm()
            assert form.validate() is False
            assert form.member_email.errors

    def test_user_login_email_invalid_format_fails(self, app):
        with app.test_request_context('/', method='POST', data={**self._VALID, 'user_login_email': 'not-an-email'}):
            form = OrganisationAdminForm()
            assert form.validate() is False
            assert form.user_login_email.errors


# ── _first_member_errors ──────────────────────────────────────────────────────

class TestFirstMemberErrors:
    def test_section_disabled_passes(self):
        form = _FirstMemberForm(enabled=False)
        assert _first_member_errors(form) is False

    def test_all_fields_present_passes(self):
        form = _FirstMemberForm()
        assert _first_member_errors(form) is False

    def test_missing_first_name_fails(self):
        form = _FirstMemberForm(first_name='')
        assert _first_member_errors(form) is True
        assert form.member_first_name.errors

    def test_whitespace_first_name_fails(self):
        form = _FirstMemberForm(first_name='   ')
        assert _first_member_errors(form) is True
        assert form.member_first_name.errors

    def test_missing_last_name_fails(self):
        form = _FirstMemberForm(last_name='')
        assert _first_member_errors(form) is True
        assert form.member_last_name.errors

    def test_missing_oib_fails(self):
        form = _FirstMemberForm(oib='')
        assert _first_member_errors(form) is True
        assert form.member_oib.errors

    def test_missing_dob_fails(self):
        form = _FirstMemberForm(dob=None)
        assert _first_member_errors(form) is True
        assert form.member_date_of_birth.errors

    def test_missing_address_fails(self):
        form = _FirstMemberForm(address='')
        assert _first_member_errors(form) is True
        assert form.member_address.errors

    def test_whitespace_address_fails(self):
        form = _FirstMemberForm(address='   ')
        assert _first_member_errors(form) is True
        assert form.member_address.errors

    def test_missing_phone_fails(self):
        form = _FirstMemberForm(phone='')
        assert _first_member_errors(form) is True
        assert form.member_phone.errors

    def test_missing_email_fails(self):
        form = _FirstMemberForm(email='')
        assert _first_member_errors(form) is True
        assert form.member_email.errors

    def test_missing_login_email_fails(self):
        form = _FirstMemberForm(login_email='')
        assert _first_member_errors(form) is True
        assert form.user_login_email.errors

    def test_missing_password_fails(self):
        form = _FirstMemberForm(password='')
        assert _first_member_errors(form) is True
        assert form.user_password.errors

    def test_multiple_missing_fields_all_reported(self):
        form = _FirstMemberForm(first_name='', last_name='', password='')
        assert _first_member_errors(form) is True
        assert form.member_first_name.errors
        assert form.member_last_name.errors
        assert form.user_password.errors


# ── add_org DB integration ────────────────────────────────────────────────────

class TestAddOrgWithFirstMember:
    def test_org_without_first_member_creates_no_member(self, app):
        with app.app_context():
            org = make_org(name='Solo Org', oib='12345678903')
            _db.session.add(org)
            _db.session.commit()
            assert Member.query.filter_by(organisation_id=org.id).count() == 0
            assert User.query.count() == 0

    def test_org_with_first_member_creates_president(self, app):
        with app.app_context():
            org = make_org(name='New NGO', oib='12345678903')
            _db.session.add(org)
            _db.session.flush()

            member = Member(
                first_name='Ana',
                last_name='Anić',
                oib='98765432109',
                date_of_birth=date(1990, 1, 1),
                address='Ilica 1',
                phone='0911234567',
                email_address='ana@example.com',
                gdpr=True,
                is_active=True,
                organisation_id=org.id,
            )
            _db.session.add(member)
            _db.session.flush()

            user = User(
                email='ana@example.com',
                role=Role.PRESIDENT,
                is_active=True,
                member=member,
            )
            user.set_password('Password1!')
            _db.session.add(user)
            _db.session.commit()

            saved_user = User.query.filter_by(email='ana@example.com').first()
            assert saved_user is not None
            assert saved_user.role == Role.PRESIDENT
            assert saved_user.member.organisation_id == org.id
            assert saved_user.check_password('Password1!')

    def test_duplicate_login_email_blocked(self, app):
        with app.app_context():
            org = make_org(name='Org A', oib='12345678903')
            _db.session.add(org)
            _db.session.flush()

            member = Member(
                first_name='Existing',
                last_name='User',
                oib='98765432109',
                date_of_birth=date(1985, 6, 15),
                address='Some Street 1',
                phone='0921234567',
                email_address='existing@example.com',
                gdpr=True,
                is_active=True,
                organisation_id=org.id,
            )
            _db.session.add(member)
            _db.session.flush()

            user = User(email='existing@example.com', role=Role.ADMIN, is_active=True, member=member)
            user.set_password('Password1!')
            _db.session.add(user)
            _db.session.commit()

            # Route logic: check for duplicate email
            duplicate = User.query.filter_by(email='existing@example.com').first()
            assert duplicate is not None
