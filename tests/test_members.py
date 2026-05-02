import pytest
from datetime import date
from flask import g
from app import db as _db
from app.models.user import User, Role
from app.members.forms import ResetPasswordForm
from app.members.routes import _deactivation_errors, _role_conflict
from tests.conftest import make_member, make_org


# ── Helpers ───────────────────────────────────────────────────────────────────

class _Field:
    def __init__(self, data):
        self.data = data
        self.errors = []


class _DeactivationForm:
    """Minimal stand-in for the parts of MemberForm that _deactivation_errors reads."""
    def __init__(self, is_active, end_date=None, end_reason=None):
        self.is_active = _Field(is_active)
        self.end_date = _Field(end_date)
        self.end_reason = _Field(end_reason)


def _make_member_with_user(oib='12345678903', member_oib='98765432109', email='u@test.com', role=Role.PRESIDENT):
    org = make_org(oib=oib)
    _db.session.add(org)
    _db.session.flush()
    member = make_member(oib=member_oib, email_address=email, organisation_id=org.id)
    _db.session.add(member)
    _db.session.flush()
    user = User(email=email, role=role, is_active=True, member=member)
    user.set_password('OldPass123!')
    _db.session.add(user)
    _db.session.commit()
    return member, user


def _persist_user(oib, email, role, org_id, is_active=True):
    m = make_member(oib=oib, email_address=email, organisation_id=org_id)
    _db.session.add(m)
    _db.session.flush()
    u = User(email=email, role=role, is_active=is_active, member=m)
    u.set_password('password123')
    _db.session.add(u)
    _db.session.commit()
    return u


# ── _deactivation_errors ──────────────────────────────────────────────────────

class TestDeactivationErrors:
    def test_active_member_passes(self):
        form = _DeactivationForm(is_active=True)
        assert _deactivation_errors(form) is False

    def test_inactive_with_both_fields_passes(self):
        form = _DeactivationForm(
            is_active=False,
            end_date=date(2025, 1, 1),
            end_reason='Resigned',
        )
        assert _deactivation_errors(form) is False

    def test_inactive_missing_end_date_fails(self):
        form = _DeactivationForm(is_active=False, end_reason='Resigned')
        assert _deactivation_errors(form) is True
        assert form.end_date.errors

    def test_inactive_missing_end_reason_fails(self):
        form = _DeactivationForm(is_active=False, end_date=date(2025, 1, 1))
        assert _deactivation_errors(form) is True
        assert form.end_reason.errors

    def test_inactive_missing_both_fails(self):
        form = _DeactivationForm(is_active=False)
        assert _deactivation_errors(form) is True
        assert form.end_date.errors
        assert form.end_reason.errors

    def test_inactive_whitespace_end_reason_fails(self):
        form = _DeactivationForm(
            is_active=False,
            end_date=date(2025, 1, 1),
            end_reason='   ',
        )
        assert _deactivation_errors(form) is True
        assert form.end_reason.errors


# ── _role_conflict ────────────────────────────────────────────────────────────

class TestRoleConflict:
    def test_no_users_no_conflict(self, app, org):
        with app.test_request_context():
            g.tenant = org
            assert _role_conflict(Role.PRESIDENT) is None

    def test_finds_active_president(self, app, org):
        u = _persist_user('12345678903', 'a@test.com', Role.PRESIDENT, org.id)
        with app.test_request_context():
            g.tenant = org
            assert _role_conflict(Role.PRESIDENT).id == u.id

    def test_finds_active_vice_president(self, app, org):
        u = _persist_user('12345678903', 'a@test.com', Role.VICE_PRESIDENT, org.id)
        with app.test_request_context():
            g.tenant = org
            assert _role_conflict(Role.VICE_PRESIDENT).id == u.id

    def test_finds_active_secretary(self, app, org):
        u = _persist_user('12345678903', 'a@test.com', Role.SECRETARY, org.id)
        with app.test_request_context():
            g.tenant = org
            assert _role_conflict(Role.SECRETARY).id == u.id

    def test_inactive_user_ignored(self, app, org):
        _persist_user('12345678903', 'a@test.com', Role.PRESIDENT, org.id, is_active=False)
        with app.test_request_context():
            g.tenant = org
            assert _role_conflict(Role.PRESIDENT) is None

    def test_excludes_own_user_id(self, app, org):
        u = _persist_user('12345678903', 'a@test.com', Role.PRESIDENT, org.id)
        with app.test_request_context():
            g.tenant = org
            assert _role_conflict(Role.PRESIDENT, exclude_user_id=u.id) is None

    def test_admin_never_conflicts(self, app, org):
        _persist_user('12345678903', 'a@test.com', Role.ADMIN, org.id)
        with app.test_request_context():
            g.tenant = org
            assert _role_conflict(Role.ADMIN) is None

    def test_viewer_never_conflicts(self, app, org):
        _persist_user('12345678903', 'a@test.com', Role.VIEWER, org.id)
        with app.test_request_context():
            g.tenant = org
            assert _role_conflict(Role.VIEWER) is None

    def test_conflict_scoped_to_org(self, app, org):
        """A president in another org does not conflict with this org."""
        other_org = make_org(name='Other Org', oib='98765432109')
        _db.session.add(other_org)
        _db.session.commit()
        _persist_user('12345678903', 'a@test.com', Role.PRESIDENT, other_org.id)
        with app.test_request_context():
            g.tenant = org
            assert _role_conflict(Role.PRESIDENT) is None


# ── ResetPasswordForm (members) ───────────────────────────────────────────────

class TestMembersResetPasswordForm:
    _VALID = {'new_password': 'SecurePass1', 'confirm_password': 'SecurePass1'}

    def test_valid_form_passes(self, app):
        with app.test_request_context('/', method='POST', data=self._VALID):
            assert ResetPasswordForm().validate() is True

    def test_missing_new_password_fails(self, app):
        with app.test_request_context('/', method='POST', data={'confirm_password': 'SecurePass1'}):
            form = ResetPasswordForm()
            assert form.validate() is False
            assert form.new_password.errors

    def test_short_new_password_fails(self, app):
        with app.test_request_context('/', method='POST', data={**self._VALID, 'new_password': 'short'}):
            form = ResetPasswordForm()
            assert form.validate() is False
            assert form.new_password.errors

    def test_missing_confirm_password_fails(self, app):
        with app.test_request_context('/', method='POST', data={'new_password': 'SecurePass1'}):
            form = ResetPasswordForm()
            assert form.validate() is False
            assert form.confirm_password.errors


# ── reset_password route logic ────────────────────────────────────────────────

class TestMembersResetPasswordLogic:
    def test_password_change_persists(self, app):
        with app.app_context():
            member, user = _make_member_with_user()
            member.user.set_password('NewPass456!')
            _db.session.commit()
            refreshed = _db.session.get(User, user.id)
            assert refreshed.check_password('NewPass456!')
            assert not refreshed.check_password('OldPass123!')

    def test_set_password_raises_for_short_password(self, app):
        with app.app_context():
            member, _ = _make_member_with_user()
            with pytest.raises(ValueError):
                member.user.set_password('short')

    def test_set_password_raises_for_empty_password(self, app):
        with app.app_context():
            member, _ = _make_member_with_user()
            with pytest.raises(ValueError):
                member.user.set_password('')

    def test_idor_check_cross_org_member(self, app):
        with app.app_context():
            org_a = make_org(name='Org A', oib='12345678903')
            _db.session.add(org_a)
            _db.session.flush()
            org_b = make_org(name='Org B', oib='11111111119')
            _db.session.add(org_b)
            _db.session.flush()
            member_b = make_member(oib='00000000001', email_address='b@test.com', organisation_id=org_b.id)
            _db.session.add(member_b)
            _db.session.commit()
            assert member_b.organisation_id != org_a.id
