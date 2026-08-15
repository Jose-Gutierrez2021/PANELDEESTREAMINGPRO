from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    session,
    flash
)

from extensions import db
from models.sale import Sale
from models.payment import Payment
from models.inventory import Inventory


payments_bp = Blueprint(
    "payments",
    __name__,
    url_prefix="/payments"
)


@payments_bp.route(
    "/<int:sale_id>",
    methods=["POST"]
)
def verify(sale_id):

    if session.get("role") != "admin":

        flash(
            "Solo el administrador puede verificar pagos."
        )

        return redirect(
            url_for("sales.index")
        )

    sale = Sale.query.get_or_404(
        sale_id
    )

    action = request.form["action"]

    if action == "verify":

        sale.payment_status = "verified"

        payment = Payment(
            sale_id=sale.id,
            amount=sale.price,
            method=sale.payment_method,
            reference=request.form.get(
                "reference"
            ),
            status="verified"
        )

        db.session.add(payment)

    elif action == "reject":

        sale.payment_status = "rejected"

        if sale.inventory:

            sale.inventory.status = "available"

            sale.inventory.expires_at = None

    db.session.commit()

    return redirect(
        url_for("sales.index")
    )
