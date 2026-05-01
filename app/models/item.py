from datetime import datetime, timezone
from app import db


class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(255), nullable=False)
    item_price = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=False)
    organisation = db.relationship('Organisation', back_populates='items')

    def __repr__(self):
        return f'<Item {self.item_name}>'
