from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.members import bp
from app.members.forms import MemberForm
from app.models.member import Member
from app.models.user import User, Role


_UNIQUE_ROLES = {Role.PRESIDENT, Role.VICE_PRESIDENT, Role.SECRETARY}


def _deactivation_errors(form):
    if form.is_active.data:
        return False
    has_error = False
    if not form.end_date.data:
        form.end_date.errors.append('End Date is required when the member is deactivated.')
        has_error = True
    if not form.end_reason.data or not form.end_reason.data.strip():
        form.end_reason.errors.append('End Reason is required when the member is deactivated.')
        has_error = True
    return has_error


def _role_conflict(role, exclude_user_id=None):
    if role not in _UNIQUE_ROLES:
        return None
    q = User.query.filter_by(role=role)
    if exclude_user_id:
        q = q.filter(User.id != exclude_user_id)
    return q.first()


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
        if _deactivation_errors(form):
            return render_template('members/form.html', form=form, title='Add Member')

        if Member.query.filter_by(oib=form.oib.data).first():
            flash('A member with this OIB already exists.', 'danger')
            return render_template('members/form.html', form=form, title='Add Member')

        if Member.query.filter_by(email_address=form.email_address.data).first():
            flash('A member with this email address already exists.', 'danger')
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
        if _deactivation_errors(form):
            return render_template('members/form.html', form=form, title='Edit Member', member=member)

        existing = Member.query.filter_by(oib=form.oib.data).first()
        if existing and existing.id != member.id:
            flash('A member with this OIB already exists.', 'danger')
            return render_template('members/form.html', form=form, title='Edit Member', member=member)

        existing_email = Member.query.filter_by(email_address=form.email_address.data).first()
        if existing_email and existing_email.id != member.id:
            flash('A member with this email address already exists.', 'danger')
            return render_template('members/form.html', form=form, title='Edit Member', member=member)

        form.populate_obj(member)

        if current_user.can_delete:
            if member.user:
                new_role = Role(form.user_role.data)
                conflict = _role_conflict(new_role, exclude_user_id=member.user.id)
                if conflict:
                    flash(f'Role {new_role.value.replace("_", " ").title()} is already assigned to {conflict.member.full_name}.', 'danger')
                    return render_template('members/form.html', form=form, title='Edit Member', member=member)
                member.user.role = new_role
                member.user.is_active = form.user_is_active.data
            elif form.new_user_email.data:
                if User.query.filter_by(email=form.new_user_email.data.lower()).first():
                    flash('A user with this email already exists.', 'danger')
                    return render_template('members/form.html', form=form, title='Edit Member', member=member)
                if not form.new_user_password.data:
                    flash('Password is required to create a user account.', 'danger')
                    return render_template('members/form.html', form=form, title='Edit Member', member=member)
                new_role = Role(form.new_user_role.data)
                conflict = _role_conflict(new_role)
                if conflict:
                    flash(f'Role {new_role.value.replace("_", " ").title()} is already assigned to {conflict.member.full_name}.', 'danger')
                    return render_template('members/form.html', form=form, title='Edit Member', member=member)
                new_user = User(
                    email=form.new_user_email.data.lower(),
                    role=new_role,
                    is_active=True,
                    member=member,
                )
                new_user.set_password(form.new_user_password.data)
                db.session.add(new_user)

        db.session.commit()
        flash(f'Member {member.full_name} updated successfully.', 'success')
        return redirect(url_for('members.view', member_id=member.id))

    if member.user and current_user.can_delete:
        form.user_role.data = member.user.role.value
        form.user_is_active.data = member.user.is_active

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
