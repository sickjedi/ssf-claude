from app import db


class Settings(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    oib = db.Column(db.String(11), nullable=True)
    iban = db.Column(db.String(34), nullable=True)

    @staticmethod
    def get():
        return Settings.query.first() or Settings()
