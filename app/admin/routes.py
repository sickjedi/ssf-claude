from functools import wraps
from flask import render_template, redirect, url_for, flash, abort, session
from flask_login import login_required, current_user
from sqlalchemy.orm import contains_eager
from app import db, limiter
from app.admin import bp
from app.admin.forms import OrganisationAdminForm, ResetPasswordForm
from app.audit import log_action
from app.models.member import Member
from app.models.organisation import Organisation
from app.models.user import User, Role


def super_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.SUPER_ADMIN:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def _first_member_errors(form):
    if not form.add_first_member.data:
        return False
    has_error = False
    str_fields = [
        (form.member_first_name, 'First Name'),
        (form.member_last_name, 'Last Name'),
        (form.member_oib, 'OIB'),
        (form.member_address, 'Address'),
        (form.member_phone, 'Phone'),
        (form.member_email, 'Email'),
        (form.user_login_email, 'Login Email'),
    ]
    for field, label in str_fields:
        if not (field.data or '').strip():
            field.errors.append(f'{label} is required.')
            has_error = True
    if not form.member_date_of_birth.data:
        form.member_date_of_birth.errors.append('Date of Birth is required.')
        has_error = True
    if not form.user_password.data:
        form.user_password.errors.append('Password is required.')
        has_error = True
    return has_error


@bp.route('/')
@login_required
@super_admin_required
def index():
    orgs = Organisation.query.order_by(Organisation.name).all()
    active_tenant_id = session.get('tenant_id')
    return render_template('admin/index.html', orgs=orgs, active_tenant_id=active_tenant_id)


@bp.route('/organisations/add', methods=['GET', 'POST'])
@login_required
@super_admin_required
def add_org():
    form = OrganisationAdminForm()
    form.is_active.data = form.is_active.data if form.is_submitted() else True

    if form.validate_on_submit():
        if Organisation.query.filter_by(oib=form.oib.data).first():
            flash('An organisation with this OIB already exists.', 'danger')
            return render_template('admin/form.html', form=form, title='Add Organisation')

        first_member = form.add_first_member.data
        if _first_member_errors(form):
            return render_template('admin/form.html', form=form, title='Add Organisation')
        if first_member:
            if User.query.filter_by(email=form.user_login_email.data.strip().lower()).first():
                form.user_login_email.errors.append('A user with this login email already exists.')
                return render_template('admin/form.html', form=form, title='Add Organisation')

        org = Organisation(
            name=form.name.data,
            oib=form.oib.data,
            address=form.address.data or None,
            city=form.city.data or None,
            iban=form.iban.data or None,
            is_active=form.is_active.data,
        )
        db.session.add(org)
        db.session.flush()

        if first_member:
            member = Member(
                first_name=form.member_first_name.data.strip(),
                last_name=form.member_last_name.data.strip(),
                oib=form.member_oib.data.strip(),
                date_of_birth=form.member_date_of_birth.data,
                address=form.member_address.data.strip(),
                phone=form.member_phone.data.strip(),
                email_address=form.member_email.data.strip(),
                gdpr=True,
                is_active=True,
                organisation_id=org.id,
            )
            db.session.add(member)
            db.session.flush()
            user = User(
                email=form.user_login_email.data.strip().lower(),
                role=Role.PRESIDENT,
                is_active=True,
                member=member,
            )
            user.set_password(form.user_password.data)
            db.session.add(user)

        db.session.commit()
        log_action('CREATE', 'Organisation', f'Created organisation {org.name} (ID: {org.id})')
        if first_member:
            log_action('CREATE', 'Member', f'Created first member {member.full_name} (ID: {member.id}) for organisation {org.name}')
        flash(f'Organisation {org.name} created.', 'success')
        return redirect(url_for('admin.index'))

    return render_template('admin/form.html', form=form, title='Add Organisation')


@bp.route('/organisations/<int:org_id>/edit', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_org(org_id):
    org = db.session.get(Organisation, org_id) or abort(404)
    form = OrganisationAdminForm(obj=org)

    if form.validate_on_submit():
        existing = Organisation.query.filter_by(oib=form.oib.data).first()
        if existing and existing.id != org.id:
            flash('An organisation with this OIB already exists.', 'danger')
            return render_template('admin/form.html', form=form, title='Edit Organisation', org=org)

        form.populate_obj(org)
        db.session.commit()
        log_action('UPDATE', 'Organisation', f'Updated organisation {org.name} (ID: {org.id})')
        flash(f'Organisation {org.name} updated.', 'success')
        return redirect(url_for('admin.index'))

    return render_template('admin/form.html', form=form, title='Edit Organisation', org=org)


@bp.route('/organisations/<int:org_id>/users')
@login_required
@super_admin_required
def org_users(org_id):
    org = db.session.get(Organisation, org_id) or abort(404)
    users = (User.query
             .join(Member, User.member_id == Member.id)
             .options(contains_eager(User.member))
             .filter(Member.organisation_id == org_id)
             .order_by(Member.last_name, Member.first_name)
             .all())
    return render_template('admin/users.html', org=org, users=users)


@bp.route('/organisations/<int:org_id>/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@super_admin_required
@limiter.limit('10 per minute')
def reset_user_password(org_id, user_id):
    org = db.session.get(Organisation, org_id) or abort(404)
    user = db.session.get(User, user_id) or abort(404)
    if not user.member or user.member.organisation_id != org_id:
        abort(404)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if form.new_password.data != form.confirm_password.data:
            form.confirm_password.errors.append('Passwords do not match.')
            return render_template('admin/reset_password.html', form=form, org=org, user=user)
        try:
            user.set_password(form.new_password.data)
        except ValueError as e:
            form.new_password.errors.append(str(e))
            return render_template('admin/reset_password.html', form=form, org=org, user=user)
        db.session.commit()
        log_action('UPDATE', 'User', f'Super admin reset password for {user.email} (ID: {user.id})')
        flash(f'Password reset for {user.member.full_name}.', 'success')
        return redirect(url_for('admin.org_users', org_id=org_id))
    return render_template('admin/reset_password.html', form=form, org=org, user=user)


@bp.route('/switch-tenant/<int:org_id>', methods=['POST'])
@login_required
@super_admin_required
def switch_tenant(org_id):
    org = db.session.get(Organisation, org_id) or abort(404)
    session['tenant_id'] = org_id
    flash(f'Now viewing data for: {org.name}', 'info')
    return redirect(url_for('members.index'))


@bp.route('/clear-tenant', methods=['POST'])
@login_required
@super_admin_required
def clear_tenant():
    session.pop('tenant_id', None)
    return redirect(url_for('admin.index'))
