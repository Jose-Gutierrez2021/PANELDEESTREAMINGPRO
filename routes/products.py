from decimal import Decimal, InvalidOperation

from flask import (
    abort,
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
from models.wholesale import WholesaleOffer
from services.security import get_csrf_token, validate_csrf_token


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
        if not validate_csrf_token():
            abort(400)

        try:
            sale_price = Decimal(request.form["sale_price"])
            cost_price = Decimal(request.form["cost_price"])
            wholesale_price = request.form.get("wholesale_price", "").strip()
            margin = Decimal(
                request.form.get("suggested_margin_percent", "40")
            )
            duration_days = int(request.form["duration_days"])
            if (
                not sale_price.is_finite()
                or not cost_price.is_finite()
                or not margin.is_finite()
                or sale_price < 0
                or cost_price < 0
                or margin < 0
                or duration_days < 1
            ):
                raise ValueError
            parsed_wholesale = (
                Decimal(wholesale_price) if wholesale_price else None
            )
            if parsed_wholesale is not None and (
                not parsed_wholesale.is_finite() or parsed_wholesale <= 0
            ):
                raise ValueError
        except (InvalidOperation, TypeError, ValueError):
            flash("Revisa los precios, el margen y la duración del producto.", "error")
            return redirect(url_for("products.index"))

        product = Product(
            name=request.form["name"].strip(),
            provider=request.form.get("provider", "").strip(),
            duration_days=duration_days,
            sale_price=sale_price,
            cost_price=cost_price,
        )

        db.session.add(product)
        db.session.flush()
        if parsed_wholesale is not None:
            db.session.add(
                WholesaleOffer(
                    product_id=product.id,
                    wholesale_price=parsed_wholesale,
                    suggested_margin_percent=margin,
                )
            )
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
        products=products,
        csrf_token=get_csrf_token(),
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
    if not validate_csrf_token():
        abort(400)

    try:
        if "sale_price" in request.form:
            product.sale_price = Decimal(request.form["sale_price"])
        if "cost_price" in request.form:
            product.cost_price = Decimal(request.form["cost_price"])
        if "duration_days" in request.form:
            product.duration_days = int(request.form["duration_days"])
        if "active" in request.form:
            product.active = request.form.get("active") in ("1", "true", "on")
        if request.form.get("wholesale_price", "").strip():
            wholesale_price = Decimal(request.form["wholesale_price"])
            margin = Decimal(
                request.form.get("suggested_margin_percent", "40")
            )
            if (
                not wholesale_price.is_finite()
                or not margin.is_finite()
                or wholesale_price <= 0
                or margin < 0
            ):
                raise ValueError
            offer = WholesaleOffer.query.filter_by(
                product_id=product.id
            ).first()
            if offer is None:
                offer = WholesaleOffer(product_id=product.id)
                db.session.add(offer)
            offer.wholesale_price = wholesale_price
            offer.suggested_margin_percent = margin

        db.session.commit()

        flash("Producto actualizado.")

    except (InvalidOperation, TypeError, ValueError):
        db.session.rollback()
        flash("Revisa los precios, el margen y la duración del producto.", "error")

    return redirect(url_for("products.index"))
