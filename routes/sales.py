from datetime import date, timedelta

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
from models.sale import Sale
from models.customer import Customer
from models.product import Product
from models.inventory import Inventory


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

        return redirect(
            url_for("auth.login")
        )

    if request.method == "POST":

        customer = Customer.query.get_or_404(
            int(request.form["customer_id"])
        )

        product = Product.query.get_or_404(
            int(request.form["product_id"])
        )

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

        start = date.today()

        expires = (
            start +
            timedelta(
                days=product.duration_days
            )
        )

        sale = Sale(
            customer_id=customer.id,
            product_id=product.id,
            inventory_id=inventory.id,
            seller_id=session["user_id"],
            expires_at=expires,
            price=product.sale_price,
            cost=product.cost_price,
            payment_method=request.form[
                "payment_method"
            ],
            payment_status="pending"
        )

        inventory.status = "sold"

        inventory.expires_at = expires

        db.session.add(sale)

        db.session.commit()

        flash(
            f"Venta #{sale.id} creada."
        )

        return redirect(
            url_for("sales.index")
        )

    customers = Customer.query.order_by(
        Customer.name
    ).all()

    products = Product.query.filter_by(
        active=True
    ).all()

    sales = Sale.query.order_by(
        Sale.id.desc()
    ).limit(100).all()

    return render_template(
        "sales/index.html",
        customers=customers,
        products=products,
        sales=sales
    )
