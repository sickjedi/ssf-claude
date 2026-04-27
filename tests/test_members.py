import pytest
from datetime import date
from app import db as _db
from app.models.user import User, Role
from app.members.routes import _deactivation_errors, _role_conflict
from tests.conftest import make_member


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


def _persist_user(oib, email, role, is_active=True):
    m = make_member(oib=oib, email_address=email)
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
    def test_no_users_no_conflict(self):
        assert _role_conflict(Role.PRESIDENT) is None

    def test_finds_active_president(self):
        u = _persist_user('12345678903', 'a@test.com', Role.PRESIDENT)
        assert _role_conflict(Role.PRESIDENT).id == u.id

    def test_finds_active_vice_president(self):
        u = _persist_user('12345678903', 'a@test.com', Role.VICE_PRESIDENT)
        assert _role_conflict(Role.VICE_PRESIDENT).id == u.id

    def test_finds_active_secretary(self):
        u = _persist_user('12345678903', 'a@test.com', Role.SECRETARY)
        assert _role_conflict(Role.SECRETARY).id == u.id

    def test_inactive_user_ignored(self):
        _persist_user('12345678903', 'a@test.com', Role.PRESIDENT, is_active=False)
        assert _role_conflict(Role.PRESIDENT) is None

    def test_excludes_own_user_id(self):
        u = _persist_user('12345678903', 'a@test.com', Role.PRESIDENT)
        assert _role_conflict(Role.PRESIDENT, exclude_user_id=u.id) is None

    def test_admin_never_conflicts(self):
        _persist_user('12345678903', 'a@test.com', Role.ADMIN)
        assert _role_conflict(Role.ADMIN) is None

    def test_viewer_never_conflicts(self):
        _persist_user('12345678903', 'a@test.com', Role.VIEWER)
        assert _role_conflict(Role.VIEWER) is None
