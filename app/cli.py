import click
from flask import current_app
from app import db
from app.models.member import Member
from app.models.user import User, Role


@current_app.cli.command('create-user')
@click.option('--first-name', prompt=True)
@click.option('--last-name', prompt=True)
@click.option('--email', prompt=True)
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--role', prompt=True,
              type=click.Choice([r.value for r in Role], case_sensitive=False),
              default='admin')
def create_user(first_name, last_name, email, password, role):
    """Create a new member with a user account."""
    if User.query.filter_by(email=email.lower()).first():
        click.echo(f'Error: user {email} already exists.')
        return

    member = Member(first_name=first_name, last_name=last_name)
    db.session.add(member)
    db.session.flush()

    user = User(email=email.lower(), role=Role(role), member=member)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    click.echo(f'Created user {email} with role [{role}].')
