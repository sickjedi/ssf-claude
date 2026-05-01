from urllib.parse import urlparse, urljoin
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.audit import log_action
from app.auth import bp
from app.auth.forms import LoginForm
from app.models.member import Member
from app.models.organisation import Organisation
from app.models.user import User, Role


def _is_safe_redirect(target):
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ('http', 'https') and ref.netloc == test.netloc


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('members.index'))

    form = LoginForm()
    orgs = Organisation.query.filter_by(is_active=True).order_by(Organisation.name).all()
    form.organisation_id.choices = [(0, '— Super Admin —')] + [(o.id, o.name) for o in orgs]

    if form.validate_on_submit():
        org_id = form.organisation_id.data
        email = form.email.data.lower()

        if org_id == 0:
            user = User.query.filter_by(email=email).first()
            if (user is None
                    or not user.check_password(form.password.data)
                    or not user.is_active
                    or user.role != Role.SUPER_ADMIN):
                flash('Invalid credentials.', 'danger')
                return redirect(url_for('auth.login'))
        else:
            user = (User.query
                    .join(Member, User.member_id == Member.id)
                    .filter(Member.organisation_id == org_id,
                            User.email == email)
                    .first())
            if (user is None
                    or not user.check_password(form.password.data)
                    or not user.is_active
                    or (user.member is not None and not user.member.is_active)):
                flash('Invalid credentials.', 'danger')
                return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        if user.role != Role.SUPER_ADMIN:
            session['tenant_id'] = org_id
        log_action('LOGIN', 'User', f'Login: {user.email}')
        next_page = request.args.get('next')
        if next_page and not _is_safe_redirect(next_page):
            next_page = None
        return redirect(next_page or url_for('members.index'))

    return render_template('auth/login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    log_action('LOGOUT', 'User', f'Logout: {current_user.email}')
    session.pop('tenant_id', None)
    logout_user()
    return redirect(url_for('auth.login'))
