import enum
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class Role(enum.Enum):
    ADMIN = 'admin'
    PRESIDENT = 'president'
    SECRETARY = 'secretary'
    VIEWER = 'viewer'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.VIEWER)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), unique=True, nullable=False)
    member = db.relationship('Member', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def can_delete(self):
        return self.role in (Role.ADMIN, Role.PRESIDENT)

    @property
    def can_write(self):
        return self.role in (Role.ADMIN, Role.PRESIDENT, Role.SECRETARY)

    def __repr__(self):
        return f'<User {self.email} [{self.role.value}]>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
