from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.members import bp
from app.members.forms import MemberForm
from app.models.member import Member


@bp.route('/')
@login_required
def index():
    members = Member.query.order_by(Member.last_name, Member.first_name).all()
    return render_template('members/index.html', members=members)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if not current_user.can_write:
        abort(403)

    form = MemberForm()
    form.is_active.data = True if form.is_active.data is None else form.is_active.data

    if form.validate_on_submit():
        if Member.query.filter_by(oib=form.oib.data).first():
            flash('A member with this OIB already exists.', 'danger')
            return render_template('members/form.html', form=form, title='Add Member')

        member = Member(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            oib=form.oib.data,
            date_of_birth=form.date_of_birth.data,
            address=form.address.data,
            phone=form.phone.data,
            email_address=form.email_address.data,
            gdpr=form.gdpr.data,
            is_active=form.is_active.data,
            end_date=form.end_date.data,
            end_reason=form.end_reason.data,
        )
        db.session.add(member)
        db.session.commit()
        flash(f'Member {member.full_name} added successfully.', 'success')
        return redirect(url_for('members.index'))

    return render_template('members/form.html', form=form, title='Add Member')


@bp.route('/<int:member_id>')
@login_required
def view(member_id):
    member = db.session.get(Member, member_id) or abort(404)
    return render_template('members/view.html', member=member)


@bp.route('/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(member_id):
    if not current_user.can_write:
        abort(403)

    member = db.session.get(Member, member_id) or abort(404)
    form = MemberForm(obj=member)

    if form.validate_on_submit():
        existing = Member.query.filter_by(oib=form.oib.data).first()
        if existing and existing.id != member.id:
            flash('A member with this OIB already exists.', 'danger')
            return render_template('members/form.html', form=form, title='Edit Member', member=member)

        form.populate_obj(member)
        db.session.commit()
        flash(f'Member {member.full_name} updated successfully.', 'success')
        return redirect(url_for('members.view', member_id=member.id))

    return render_template('members/form.html', form=form, title='Edit Member', member=member)


@bp.route('/<int:member_id>/delete', methods=['POST'])
@login_required
def delete(member_id):
    if not current_user.can_delete:
        abort(403)

    member = db.session.get(Member, member_id) or abort(404)

    if member.user:
        flash('Cannot delete a member who has a user account. Remove the user account first.', 'danger')
        return redirect(url_for('members.view', member_id=member.id))

    name = member.full_name
    db.session.delete(member)
    db.session.commit()
    flash(f'Member {name} deleted.', 'success')
    return redirect(url_for('members.index'))
