from datetime import date, timedelta

from flask import (
    abort,
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from extensions import db
from models.customer import Customer, SYSTEM_WALK_IN_CUSTOMER_MARKER
from models.inventory import Inventory
from models.payment import Payment
from models.product import Product
from models.sale import Sale
from services.wompi import is_configured
from services.security import get_csrf_token, validate_csrf_token


sales_bp = Blueprint(
    "sales",
    __name__,
    url_prefix="/sales"
)


@sales_bp.route(
    "/",
    methods=["GET", "POST"]
)
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("role") not in {"admin", "seller"}:
        return redirect(url_for("reseller.index"))

    if request.method == "POST":
        if not validate_csrf_token():
            abort(400)

        if not is_configured():
            flash(
                "Configura las llaves de Wompi antes de registrar ventas PSE.",
                "error",
            )
            return redirect(url_for("sales.index"))

        product_id = request.form.get("product_id", "")
        if not product_id.isdigit():
            flash("Selecciona un producto válido.", "error")
            return redirect(url_for("sales.index"))

        product = Product.query.get_or_404(int(product_id))
        inventory = Inventory.query.filter_by(
            product_id=product.id,
            status="available",
        ).first()
        if not inventory:
            flash("No hay inventario disponible.", "error")
            return redirect(url_for("sales.index"))

        customer = Customer.query.filter_by(
            notes=SYSTEM_WALK_IN_CUSTOMER_MARKER
        ).first()
        if not customer:
            customer = Customer(
                name="Consumidor final",
                notes=SYSTEM_WALK_IN_CUSTOMER_MARKER,
            )
            db.session.add(customer)
            db.session.flush()

        expires = date.today() + timedelta(days=product.duration_days)
        sale = Sale(
            customer_id=customer.id,
            product_id=product.id,
            inventory_id=inventory.id,
            seller_id=session["user_id"],
            expires_at=expires,
            price=product.sale_price,
            cost=product.cost_price,
            payment_method="PSE",
            payment_status="pending",
        )
        inventory.status = "sold"
        inventory.expires_at = expires
        db.session.add(sale)
        db.session.commit()

        flash(f"Pedido #{sale.id} registrado. Completa el pago por PSE.", "info")
        return redirect(
            url_for("payments.pse_checkout", sale_id=sale.id)
        )

    products = Product.query.filter_by(active=True).all()
    sales = Sale.query.order_by(Sale.id.desc()).limit(100).all()
    pending_payment_sale_ids = {
        payment.sale_id
        for payment in Payment.query.filter_by(status="pending").all()
    }

    return render_template(
        "sales/index.html",
        products=products,
        sales=sales,
        pse_configured=is_configured(),
        pending_payment_sale_ids=pending_payment_sale_ids,
        csrf_token=get_csrf_token(),
    )
