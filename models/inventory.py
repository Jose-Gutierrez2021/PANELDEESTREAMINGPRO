from extensions import db


class Inventory(db.Model):

    __tablename__ = "inventory"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    reference = db.Column(
        db.String(150),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="available"
    )

    expires_at = db.Column(
        db.Date
    )

    product = db.relationship(
        "Product"
    )
