from datetime import date, timedelta

from flask import (
    Blueprint,
    abort,
    redirect,
    url_for,
    flash,
    session
)

from extensions import db
from models.sale import Sale
from models.inventory import Inventory
from services.wompi import is_configured
from services.security import validate_csrf_token


renewals_bp = Blueprint(
    "renewals",
    __name__,
    url_prefix="/renewals"
)


@renewals_bp.route(
    "/<int:sale_id>",
    methods=["POST"]
)
def renew(sale_id):

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    if session.get("role") not in {"admin", "seller"}:
        return redirect(url_for("reseller.index"))

    if not validate_csrf_token():
        abort(400)

    old_sale = Sale.query.get_or_404(
        sale_id
    )

    if old_sale.payment_status != "verified":
        flash(
            "Solo puedes renovar una venta con el pago PSE confirmado.",
            "error",
        )
        return redirect(
            url_for("sales.index")
        )

    if not is_configured():
        flash(
            "Configura las llaves de Wompi antes de crear renovaciones PSE.",
            "error",
        )
        return redirect(
            url_for("sales.index")
        )

    product = old_sale.product

    inventory = Inventory.query.filter_by(
        product_id=product.id,
        status="available"
    ).first()

    if not inventory:

        flash(
            "No hay inventario disponible."
        )

        return redirect(
            url_for("sales.index")
        )

    base_date = max(
        date.today(),
        old_sale.expires_at
    )

    expiration = (
        base_date +
        timedelta(
            days=product.duration_days
        )
    )

    inventory.status = "sold"

    inventory.expires_at = expiration

    new_sale = Sale(
        customer_id=old_sale.customer_id,
        product_id=old_sale.product_id,
        inventory_id=inventory.id,
        seller_id=session["user_id"],
        expires_at=expiration,
        price=product.sale_price,
        cost=product.cost_price,
        payment_method="PSE",
        payment_status="pending"
    )

    db.session.add(new_sale)

    db.session.commit()

    flash(
        f"Renovación #{new_sale.id} creada. Completa el pago por PSE.",
        "info",
    )
    return redirect(
        url_for("payments.pse_checkout", sale_id=new_sale.id)
    )
