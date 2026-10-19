from decimal import Decimal, InvalidOperation
import secrets

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from extensions import db
from models.wallet import Wallet, WalletMovement, WalletTopUp
from services.security import get_csrf_token, validate_csrf_token
from services.wompi import is_configured


wallet_bp = Blueprint("wallet", __name__, url_prefix="/wallet")
MINIMUM_TOPUP_COP = Decimal("10000")
MAXIMUM_WALLET_COP = Decimal("9999999999.99")


def _get_wallet(user_id):
    wallet = Wallet.query.filter_by(user_id=user_id).first()
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=Decimal("0"))
        db.session.add(wallet)
        db.session.flush()
    return wallet


@wallet_bp.route("/", methods=["GET", "POST"])
def index():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("auth.login"))
    if session.get("role") == "admin":
        flash("La cartera está disponible para cuentas de revendedor.", "error")
        return redirect(url_for("dashboard.index"))

    wallet = _get_wallet(user_id)
    if request.method == "POST":
        if not validate_csrf_token():
            abort(400)
        if not is_configured():
            flash("Los pagos PSE aún no están configurados.", "error")
            return redirect(url_for("wallet.index"))

        try:
            amount = Decimal(request.form.get("amount", "").strip())
        except (InvalidOperation, ValueError):
            amount = Decimal("0")

        if (
            not amount.is_finite()
            or amount != amount.to_integral_value()
            or amount < MINIMUM_TOPUP_COP
            or amount > MAXIMUM_WALLET_COP
        ):
            flash("La recarga mínima es $10.000 COP y debe ser en pesos enteros.", "error")
            return redirect(url_for("wallet.index"))

        topup = WalletTopUp(
            user_id=user_id,
            amount=amount,
            status="created",
            reference=f"WT{secrets.token_hex(12)}",
        )
        db.session.add(topup)
        db.session.commit()
        return redirect(
            url_for("payments.topup_pse_checkout", topup_id=topup.id)
        )

    topups = WalletTopUp.query.filter_by(user_id=user_id).order_by(
        WalletTopUp.created_at.desc(),
        WalletTopUp.id.desc(),
    ).limit(25).all()
    movements = WalletMovement.query.filter_by(user_id=user_id).order_by(
        WalletMovement.created_at.desc(),
        WalletMovement.id.desc(),
    ).limit(25).all()
    return render_template(
        "wallet/index.html",
        wallet=wallet,
        topups=topups,
        movements=movements,
        pse_configured=is_configured(),
        minimum_topup=MINIMUM_TOPUP_COP,
        csrf_token=get_csrf_token(),
    )
