from flask import render_template, flash, abort
from flask_login import login_required, current_user
from app import db
from app.audit import log_action
from app.settings import bp
from app.settings.forms import SettingsForm
from app.models.settings import Settings


@bp.route('/', methods=['GET', 'POST'])
@login_required
def edit():
    if not current_user.can_delete:
        abort(403)

    settings = Settings.query.first()
    if settings is None:
        settings = Settings()

    form = SettingsForm(obj=settings)

    if form.validate_on_submit():
        form.populate_obj(settings)
        if settings.id is None:
            db.session.add(settings)
        db.session.commit()
        log_action('UPDATE', 'Settings', 'Updated organization settings')
        flash('Settings saved.', 'success')

    return render_template('settings/edit.html', form=form)
