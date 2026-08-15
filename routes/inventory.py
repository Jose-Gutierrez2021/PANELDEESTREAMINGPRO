from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from extensions import db
from models.inventory import Inventory
from models.product import Product


inventory_bp = Blueprint(
    "inventory",
    __name__,
    url_prefix="/inventory"
)


@inventory_bp.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if session.get("role") != "admin":

        flash(
            "Solo el administrador puede gestionar inventario."
        )

        return redirect(
            url_for("dashboard.index")
        )

    if request.method == "POST":

        item = Inventory(
            product_id=int(
                request.form["product_id"]
            ),
            reference=request.form["reference"],
            status="available"
        )

        db.session.add(item)

        db.session.commit()

        flash(
            "Elemento agregado al inventario."
        )

        return redirect(
            url_for("inventory.index")
        )

    items = Inventory.query.order_by(
        Inventory.id.desc()
    ).all()

    products = Product.query.filter_by(
        active=True
    ).all()

    return render_template(
        "inventory/index.html",
        items=items,
        products=products
    )
