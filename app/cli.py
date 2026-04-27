import click
from datetime import date
from flask import current_app
from app import db
from app.models.member import Member
from app.models.user import User, Role


@current_app.cli.command('create-user')
@click.option('--first-name', prompt=True)
@click.option('--last-name', prompt=True)
@click.option('--oib', prompt=True)
@click.option('--date-of-birth', prompt=True, help='YYYY-MM-DD')
@click.option('--address', prompt=True)
@click.option('--phone', prompt=True)
@click.option('--member-email', prompt='Member contact email')
@click.option('--login-email', prompt='Login email (for user account)')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--role', prompt=True,
              type=click.Choice([r.value for r in Role], case_sensitive=False),
              default='admin')
def create_user(first_name, last_name, oib, date_of_birth, address, phone,
                member_email, login_email, password, role):
    """Create a new member with a user account."""
    if User.query.filter_by(email=login_email.lower()).first():
        click.echo(f'Error: user {login_email} already exists.')
        return

    if Member.query.filter_by(oib=oib).first():
        click.echo(f'Error: member with OIB {oib} already exists.')
        return

    if Member.query.filter_by(email_address=member_email.lower()).first():
        click.echo(f'Error: member with email {member_email} already exists.')
        return

    try:
        dob = date.fromisoformat(date_of_birth)
    except ValueError:
        click.echo('Error: date-of-birth must be in YYYY-MM-DD format.')
        return

    if not password or len(password) < 8:
        click.echo('Error: password must be at least 8 characters.')
        return

    member = Member(
        first_name=first_name,
        last_name=last_name,
        oib=oib,
        date_of_birth=dob,
        address=address,
        phone=phone,
        email_address=member_email.lower(),
        gdpr=True,
        is_active=True,
    )
    db.session.add(member)
    db.session.flush()

    user = User(email=login_email.lower(), role=Role(role), member=member)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    click.echo(f'Created user {login_email} with role [{role}].')
