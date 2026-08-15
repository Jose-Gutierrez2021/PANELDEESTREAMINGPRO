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
from models.product import Product


products_bp = Blueprint(
    "products",
    __name__,
    url_prefix="/products"
)


@products_bp.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if session.get("role") != "admin":

        flash(
            "Solo el administrador puede gestionar productos."
        )

        return redirect(
            url_for("dashboard.index")
        )

    if request.method == "POST":

        product = Product(
            name=request.form["name"],
            provider=request.form.get("provider"),
            duration_days=int(
                request.form["duration_days"]
            ),
            sale_price=float(
                request.form["sale_price"]
            ),
            cost_price=float(
                request.form["cost_price"]
            )
        )

        db.session.add(product)

        db.session.commit()

        flash(
            "Producto creado."
        )

        return redirect(
            url_for("products.index")
        )

    products = Product.query.order_by(
        Product.id.desc()
    ).all()

    return render_template(
        "products/index.html",
        products=products
    )


@products_bp.route(
    "/<int:product_id>/edit",
    methods=["POST"]
)
def edit_product(product_id):

    if session.get("role") != "admin":

        flash(
            "Solo el administrador puede editar productos."
        )

        return redirect(
            url_for("dashboard.index")
        )

    product = Product.query.get_or_404(product_id)

    # Only update provided fields
    try:
        if "sale_price" in request.form:
            product.sale_price = float(request.form["sale_price"])
        if "cost_price" in request.form:
            product.cost_price = float(request.form["cost_price"])
        if "duration_days" in request.form:
            product.duration_days = int(request.form["duration_days"])
        # optional: active flag
        if "active" in request.form:
            product.active = request.form.get("active") in ("1", "true", "on")

        db.session.commit()

        flash("Producto actualizado.")

    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar: {e}")

    return redirect(url_for("products.index"))
