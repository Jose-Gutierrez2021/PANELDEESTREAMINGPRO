from extensions import db


class ResellerOrder(db.Model):
    __tablename__ = "reseller_orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
    )
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User")
    product = db.relationship("Product")


class ResellerStock(db.Model):
    __tablename__ = "reseller_stock"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("reseller_orders.id"),
        nullable=False,
    )
    inventory_id = db.Column(
        db.Integer,
        db.ForeignKey("inventory.id"),
        nullable=False,
        unique=True,
    )

    user = db.relationship("User")
    order = db.relationship("ResellerOrder")
    inventory = db.relationship("Inventory")


class ResellerPricing(db.Model):
    __tablename__ = "reseller_pricing"
    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
    )
    resale_price = db.Column(db.Numeric(12, 2), nullable=False)
    margin_percent = db.Column(db.Numeric(7, 2), nullable=False)

    user = db.relationship("User")
    product = db.relationship("Product")
