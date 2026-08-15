from extensions import db


class Sale(db.Model):

    __tablename__ = "sales"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    inventory_id = db.Column(
        db.Integer,
        db.ForeignKey("inventory.id")
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    sale_date = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    expires_at = db.Column(
        db.Date,
        nullable=False
    )

    price = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    cost = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    payment_method = db.Column(
        db.String(50)
    )

    payment_status = db.Column(
        db.String(30),
        default="pending"
    )

    status = db.Column(
        db.String(30),
        default="active"
    )

    customer = db.relationship(
        "Customer"
    )

    product = db.relationship(
        "Product"
    )

    inventory = db.relationship(
        "Inventory"
    )

    seller = db.relationship(
        "User"
    )
