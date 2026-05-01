from datetime import datetime, timezone
from app import db


class Organisation(db.Model):
    __tablename__ = 'organisations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    oib = db.Column(db.String(11), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    iban = db.Column(db.String(34), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    members = db.relationship('Member', back_populates='organisation', lazy='dynamic')
    customers = db.relationship('Customer', back_populates='organisation', lazy='dynamic')
    invoices = db.relationship('Invoice', back_populates='organisation', lazy='dynamic')
    items = db.relationship('Item', back_populates='organisation', lazy='dynamic')

    def __repr__(self):
        return f'<Organisation {self.name}>'
