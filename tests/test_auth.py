import pytest
from app.auth.routes import _is_safe_redirect
from app.auth.forms import LoginForm


class TestIsSafeRedirect:
    def test_relative_path_is_safe(self, app):
        with app.test_request_context('/', base_url='http://localhost'):
            assert _is_safe_redirect('/members/') is True

    def test_same_host_absolute_is_safe(self, app):
        with app.test_request_context('/', base_url='http://localhost'):
            assert _is_safe_redirect('http://localhost/members/') is True

    def test_external_host_is_not_safe(self, app):
        with app.test_request_context('/', base_url='http://localhost'):
            assert _is_safe_redirect('http://evil.example.com/steal') is False

    def test_different_port_is_not_safe(self, app):
        with app.test_request_context('/', base_url='http://localhost'):
            assert _is_safe_redirect('http://localhost:9999/members/') is False

    def test_javascript_scheme_is_not_safe(self, app):
        with app.test_request_context('/', base_url='http://localhost'):
            assert _is_safe_redirect('javascript:alert(1)') is False

    def test_empty_string_is_safe(self, app):
        with app.test_request_context('/', base_url='http://localhost'):
            assert _is_safe_redirect('') is True


class TestLoginForm:
    def test_organisation_id_zero_is_valid(self, app):
        with app.test_request_context('/', method='POST', data={
            'organisation_id': '0',
            'email': 'admin@test.com',
            'password': 'secret',
        }):
            form = LoginForm()
            form.organisation_id.choices = [(0, '— Super Admin —')]
            assert form.validate() is True

    def test_missing_organisation_id_is_invalid(self, app):
        with app.test_request_context('/', method='POST', data={
            'email': 'admin@test.com',
            'password': 'secret',
        }):
            form = LoginForm()
            form.organisation_id.choices = [(0, '— Super Admin —')]
            assert form.validate() is False

    def test_missing_email_is_invalid(self, app):
        with app.test_request_context('/', method='POST', data={
            'organisation_id': '0',
            'password': 'secret',
        }):
            form = LoginForm()
            form.organisation_id.choices = [(0, '— Super Admin —')]
            assert form.validate() is False

    def test_missing_password_is_invalid(self, app):
        with app.test_request_context('/', method='POST', data={
            'organisation_id': '0',
            'email': 'admin@test.com',
        }):
            form = LoginForm()
            form.organisation_id.choices = [(0, '— Super Admin —')]
            assert form.validate() is False

    def test_invalid_email_format_is_invalid(self, app):
        with app.test_request_context('/', method='POST', data={
            'organisation_id': '0',
            'email': 'not-an-email',
            'password': 'secret',
        }):
            form = LoginForm()
            form.organisation_id.choices = [(0, '— Super Admin —')]
            assert form.validate() is False
