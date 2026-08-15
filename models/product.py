from extensions import db


class Product(db.Model):

    __tablename__ = "products"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    provider = db.Column(
        db.String(100)
    )

    duration_days = db.Column(
        db.Integer,
        nullable=False,
        default=30
    )

    sale_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    cost_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    active = db.Column(
        db.Boolean,
        default=True
    )
