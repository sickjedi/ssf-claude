from datetime import datetime, timezone
from app import db


class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    oib = db.Column(db.String(11), nullable=False, unique=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email_address = db.Column(db.String(255), nullable=False)
    gdpr = db.Column(db.Boolean, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    end_date = db.Column(db.Date, nullable=True)
    end_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', back_populates='member', uselist=False)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<Member {self.full_name}>'
