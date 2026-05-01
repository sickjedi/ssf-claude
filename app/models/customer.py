from datetime import datetime, timezone
from app import db


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    customer_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=False)
    organisation = db.relationship('Organisation', back_populates='customers')
    invoices = db.relationship('Invoice', back_populates='customer', lazy='select')

    __mapper_args__ = {
        'polymorphic_on': customer_type,
        'polymorphic_identity': 'customer',
    }

    @property
    def display_name(self):
        raise NotImplementedError

    def __repr__(self):
        return f'<Customer {self.display_name}>'


class PersonCustomer(Customer):
    customer_name = db.Column(db.String(255), nullable=True)
    customer_address = db.Column(db.String(255), nullable=True)

    __mapper_args__ = {'polymorphic_identity': 'person'}

    @property
    def display_name(self):
        return self.customer_name or '(No name)'


class CompanyCustomer(Customer):
    company_name = db.Column(db.String(255), nullable=True)
    company_address = db.Column(db.String(255), nullable=True)
    company_oib = db.Column(db.String(11), nullable=True)

    __mapper_args__ = {'polymorphic_identity': 'company'}

    @property
    def display_name(self):
        return self.company_name or '(No name)'
