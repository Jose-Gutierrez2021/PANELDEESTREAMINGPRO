from extensions import db


SYSTEM_WALK_IN_CUSTOMER_MARKER = "__system_walk_in_customer__"


class Customer(db.Model):

    __tablename__ = "customers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    phone = db.Column(
        db.String(40)
    )

    email = db.Column(
        db.String(150)
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
