import click
from datetime import date
from flask import current_app
from app import db
from app.models.member import Member
from app.models.organisation import Organisation
from app.models.user import User, Role
from app.validators import check_password_strength


@current_app.cli.command('create-org')
@click.option('--name', prompt=True)
@click.option('--oib', prompt=True)
@click.option('--address', default='', prompt=False)
@click.option('--city', default='', prompt=False)
@click.option('--iban', default='', prompt=False)
def create_org(name, oib, address, city, iban):
    """Create a new Organisation (tenant)."""
    if Organisation.query.filter_by(oib=oib).first():
        click.echo(f'Error: organisation with OIB {oib} already exists.')
        return

    org = Organisation(
        name=name,
        oib=oib,
        address=address or None,
        city=city or None,
        iban=iban or None,
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    click.echo(f'Created organisation "{name}" (ID: {org.id}).')


@current_app.cli.command('create-user')
@click.option('--super-admin', is_flag=True, default=False,
              help='Create a super-admin user (no member record required)')
@click.option('--org-oib', default=None, help='OIB of the organisation the member belongs to')
@click.option('--first-name', prompt=lambda: not click.get_current_context().params.get('super_admin'),
              default='', prompt_required=False)
@click.option('--last-name', prompt=lambda: not click.get_current_context().params.get('super_admin'),
              default='', prompt_required=False)
@click.option('--oib', 'member_oib', default=None, help='Member OIB (11 digits)')
@click.option('--date-of-birth', default=None, help='YYYY-MM-DD')
@click.option('--address', default='')
@click.option('--phone', default='')
@click.option('--member-email', default=None, help='Member contact email')
@click.option('--login-email', prompt='Login email (for user account)')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--role', prompt=True,
              type=click.Choice([r.value for r in Role], case_sensitive=False),
              default='admin')
def create_user(super_admin, org_oib, first_name, last_name, member_oib,
                date_of_birth, address, phone, member_email,
                login_email, password, role):
    """Create a new user account (with member record unless --super-admin)."""
    if User.query.filter_by(email=login_email.lower()).first():
        click.echo(f'Error: user {login_email} already exists.')
        return

    error = check_password_strength(password)
    if error:
        click.echo(f'Error: {error}')
        return

    if super_admin:
        user = User(email=login_email.lower(), role=Role.SUPER_ADMIN)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Created super-admin user {login_email}.')
        return

    # Regular user: needs an org and a member record
    if not org_oib:
        click.echo('Error: --org-oib is required for non-super-admin users.')
        return

    org = Organisation.query.filter_by(oib=org_oib).first()
    if not org:
        click.echo(f'Error: organisation with OIB {org_oib} not found.')
        return

    if not member_oib:
        member_oib = click.prompt('Member OIB (11 digits)')
    if not date_of_birth:
        date_of_birth = click.prompt('Date of birth (YYYY-MM-DD)')
    if not first_name:
        first_name = click.prompt('First name')
    if not last_name:
        last_name = click.prompt('Last name')
    if not address:
        address = click.prompt('Address')
    if not phone:
        phone = click.prompt('Phone')
    if not member_email:
        member_email = click.prompt('Member contact email')

    if Member.query.filter_by(oib=member_oib, organisation_id=org.id).first():
        click.echo(f'Error: member with OIB {member_oib} already exists in this organisation.')
        return

    if Member.query.filter_by(email_address=member_email.lower(), organisation_id=org.id).first():
        click.echo(f'Error: member with email {member_email} already exists in this organisation.')
        return

    try:
        dob = date.fromisoformat(date_of_birth)
    except ValueError:
        click.echo('Error: date-of-birth must be in YYYY-MM-DD format.')
        return

    member = Member(
        first_name=first_name,
        last_name=last_name,
        oib=member_oib,
        date_of_birth=dob,
        address=address,
        phone=phone,
        email_address=member_email.lower(),
        gdpr=True,
        is_active=True,
        organisation_id=org.id,
    )
    db.session.add(member)
    db.session.flush()

    user = User(email=login_email.lower(), role=Role(role), member=member)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    click.echo(f'Created user {login_email} with role [{role}] in organisation "{org.name}".')
