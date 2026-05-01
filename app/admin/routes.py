from functools import wraps
from flask import render_template, redirect, url_for, flash, abort, session
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.admin.forms import OrganisationAdminForm
from app.audit import log_action
from app.models.organisation import Organisation
from app.models.user import Role


def super_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.SUPER_ADMIN:
            abort(403)
        return f(*args, **kwargs)
    return decorated


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

        org = Organisation(
            name=form.name.data,
            oib=form.oib.data,
            address=form.address.data or None,
            city=form.city.data or None,
            iban=form.iban.data or None,
            is_active=form.is_active.data,
        )
        db.session.add(org)
        db.session.commit()
        log_action('CREATE', 'Organisation', f'Created organisation {org.name} (ID: {org.id})')
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
