from extensions import db


class WholesaleOffer(db.Model):
    __tablename__ = "wholesale_offers"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        unique=True,
    )
    wholesale_price = db.Column(db.Numeric(12, 2), nullable=False)
    suggested_margin_percent = db.Column(
        db.Numeric(7, 2),
        nullable=False,
        default=40,
    )

    product = db.relationship("Product", backref=db.backref(
        "wholesale_offer",
        uselist=False,
        cascade="all, delete-orphan",
    ))
