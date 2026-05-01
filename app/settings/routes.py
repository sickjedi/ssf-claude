from flask import render_template, flash, abort, g
from flask_login import login_required, current_user
from app import db
from app.audit import log_action
from app.settings import bp
from app.settings.forms import OrganisationForm
from app.tenant import require_tenant


@bp.route('/', methods=['GET', 'POST'])
@login_required
def edit():
    if not current_user.can_delete:
        abort(403)
    require_tenant()

    org = g.tenant
    form = OrganisationForm(obj=org)

    if form.validate_on_submit():
        form.populate_obj(org)
        db.session.commit()
        log_action('UPDATE', 'Organisation', f'Updated organisation settings (ID: {org.id})')
        flash('Settings saved.', 'success')

    return render_template('settings/edit.html', form=form)
