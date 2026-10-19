from extensions import db


class Wallet(db.Model):
    __tablename__ = "wallets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    user = db.relationship("User")


class WalletTopUp(db.Model):
    __tablename__ = "wallet_topups"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="created")
    reference = db.Column(db.String(150), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User")


class WalletMovement(db.Model):
    __tablename__ = "wallet_movements"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    movement_type = db.Column(db.String(30), nullable=False)
    topup_id = db.Column(
        db.Integer,
        db.ForeignKey("wallet_topups.id"),
        unique=True,
    )
    reseller_order_id = db.Column(
        db.Integer,
        db.ForeignKey("reseller_orders.id"),
        unique=True,
    )
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User")
    topup = db.relationship("WalletTopUp")
