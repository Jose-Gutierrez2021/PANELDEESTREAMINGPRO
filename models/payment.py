from extensions import db


class Payment(db.Model):

    __tablename__ = "payments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    sale_id = db.Column(
        db.Integer,
        db.ForeignKey("sales.id"),
        nullable=False
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    method = db.Column(
        db.String(50)
    )

    reference = db.Column(
        db.String(150)
    )

    status = db.Column(
        db.String(30),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    sale = db.relationship(
        "Sale"
    )
