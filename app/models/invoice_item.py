from app import db


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=True)
    item_name = db.Column(db.String(255), nullable=False)
    item_price = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    item_quantity = db.Column(db.Integer, nullable=False)

    invoice = db.relationship('Invoice', back_populates='items')
    item = db.relationship('Item')

    @property
    def subtotal(self):
        return self.item_price * self.item_quantity

    def __repr__(self):
        return f'<InvoiceItem {self.item_name}>'
