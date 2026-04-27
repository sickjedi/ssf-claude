import os

# Must be set before any app import triggers config.py parsing.
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('DATABASE_URL', '')

import pytest
from datetime import date
from app import create_app, db as _db
from app.models.member import Member


class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


@pytest.fixture(scope='session')
def app():
    application = create_app(TestConfig)
    ctx = application.app_context()
    ctx.push()
    _db.create_all()
    yield application
    _db.drop_all()
    ctx.pop()


@pytest.fixture(autouse=True)
def clean_tables(app):
    """Wipe all rows after every test, preserving the schema."""
    yield
    _db.session.rollback()
    for table in reversed(_db.metadata.sorted_tables):
        _db.session.execute(table.delete())
    _db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


def make_member(**kwargs) -> Member:
    """Return an unsaved Member with sensible defaults."""
    defaults = dict(
        first_name='Test',
        last_name='User',
        oib='12345678903',
        date_of_birth=date(1990, 1, 1),
        address='Test Street 1',
        phone='0911234567',
        email_address='test@example.com',
        gdpr=True,
        is_active=True,
    )
    defaults.update(kwargs)
    return Member(**defaults)
