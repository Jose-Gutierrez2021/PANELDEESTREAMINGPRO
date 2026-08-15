from datetime import date, timedelta

from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    session
)

from extensions import db
from models.sale import Sale
from models.inventory import Inventory


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

    old_sale = Sale.query.get_or_404(
        sale_id
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
        payment_method=old_sale.payment_method,
        payment_status="pending"
    )

    db.session.add(new_sale)

    db.session.commit()

    flash(
        f"Renovación #{new_sale.id} creada."
    )

    return redirect(
        url_for("sales.index")
    )
