from datetime import datetime, timezone
from app import db


class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=False)
    organisation = db.relationship('Organisation', back_populates='invoices')
    customer = db.relationship('Customer', back_populates='invoices')
    items = db.relationship('InvoiceItem', back_populates='invoice', cascade='all, delete-orphan')

    @property
    def total(self):
        return sum(item.subtotal for item in self.items)

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
