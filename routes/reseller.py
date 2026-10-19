from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

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
from models.inventory import Inventory
from models.reseller import ResellerOrder, ResellerPricing, ResellerStock
from models.wallet import Wallet, WalletMovement
from models.wholesale import WholesaleOffer
from services.security import get_csrf_token, validate_csrf_token


reseller_bp = Blueprint("reseller", __name__, url_prefix="/reseller")
MONEY_QUANTUM = Decimal("0.01")


def _decimal(value):
    try:
        result = Decimal(value.strip())
    except (AttributeError, InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def _money(value):
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def _reseller_user_id():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    if session.get("role") == "admin":
        abort(403)
    return user_id


@reseller_bp.route("/", methods=["GET", "POST"])
def index():
    user_id = _reseller_user_id()
    if user_id is None:
        return redirect(url_for("auth.login"))

    wallet = Wallet.query.filter_by(user_id=user_id).first()
    products = []
    for offer in WholesaleOffer.query.join(WholesaleOffer.product).filter_by(
        active=True
    ).order_by(WholesaleOffer.id).all():
        product = offer.product
        pricing = ResellerPricing.query.filter_by(
            user_id=user_id,
            product_id=product.id,
        ).first()
        available_count = Inventory.query.filter_by(
            product_id=product.id,
            status="available",
        ).count()
        margin = (
            pricing.margin_percent
            if pricing
            else offer.suggested_margin_percent
        )
        resale_price = (
            pricing.resale_price
            if pricing
            else _money(
                offer.wholesale_price
                * (Decimal("1") + Decimal(margin) / Decimal("100"))
            )
        )
        products.append(
            {
                "product": product,
                "offer": offer,
                "available_count": available_count,
                "margin": margin,
                "resale_price": resale_price,
            }
        )

    stock = ResellerStock.query.filter_by(user_id=user_id).join(
        ResellerStock.inventory
    ).order_by(ResellerStock.id.desc()).all()

    return render_template(
        "reseller/index.html",
        wallet=wallet,
        products=products,
        stock=stock,
        csrf_token=get_csrf_token(),
    )


@reseller_bp.route("/buy", methods=["POST"])
def buy():
    user_id = _reseller_user_id()
    if user_id is None:
        return redirect(url_for("auth.login"))
    if not validate_csrf_token():
        abort(400)

    product_id = request.form.get("product_id", "")
    quantity_value = request.form.get("quantity", "")
    if not product_id.isdigit() or not quantity_value.isdigit():
        flash("Selecciona un producto y una cantidad válidos.", "error")
        return redirect(url_for("reseller.index"))
    quantity = int(quantity_value)
    if quantity < 1:
        flash("La cantidad debe ser al menos una unidad.", "error")
        return redirect(url_for("reseller.index"))

    offer = WholesaleOffer.query.filter_by(
        product_id=int(product_id)
    ).first()
    if offer is None or not offer.product.active:
        flash("Ese producto no tiene un precio mayorista activo.", "error")
        return redirect(url_for("reseller.index"))

    wallet = Wallet.query.filter_by(user_id=user_id).with_for_update().first()
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=Decimal("0"))
        db.session.add(wallet)
        db.session.flush()

    total = _money(offer.wholesale_price * quantity)
    if wallet.balance < total:
        flash("Tu saldo no alcanza para esa compra. Recarga tu cartera primero.", "error")
        return redirect(url_for("reseller.index"))

    items = Inventory.query.filter_by(
        product_id=offer.product_id,
        status="available",
    ).order_by(Inventory.id).with_for_update().limit(quantity).all()
    if len(items) != quantity:
        flash("No hay suficientes unidades disponibles para completar la compra.", "error")
        return redirect(url_for("reseller.index"))

    order = ResellerOrder(
        user_id=user_id,
        product_id=offer.product_id,
        quantity=quantity,
        unit_price=offer.wholesale_price,
        total=total,
    )
    db.session.add(order)
    db.session.flush()
    wallet.balance -= total
    for item in items:
        item.status = "assigned"
        db.session.add(
            ResellerStock(
                user_id=user_id,
                order_id=order.id,
                inventory_id=item.id,
            )
        )
    db.session.add(
        WalletMovement(
            user_id=user_id,
            amount=-total,
            movement_type="wholesale_purchase",
            reseller_order_id=order.id,
        )
    )
    db.session.commit()
    flash(
        f"Compra #{order.id} completada: {quantity} unidad(es) asignada(s) a tu cuenta.",
        "success",
    )
    return redirect(url_for("reseller.index"))


@reseller_bp.route("/pricing/<int:product_id>", methods=["POST"])
def update_pricing(product_id):
    user_id = _reseller_user_id()
    if user_id is None:
        return redirect(url_for("auth.login"))
    if not validate_csrf_token():
        abort(400)

    offer = WholesaleOffer.query.filter_by(product_id=product_id).first_or_404()
    pricing = ResellerPricing.query.filter_by(
        user_id=user_id,
        product_id=product_id,
    ).first()
    field = request.form.get("pricing_field")

    if field == "margin":
        margin = _decimal(request.form.get("margin_percent", ""))
        if margin is None or margin < 0:
            flash("El margen debe ser un porcentaje válido mayor o igual a 0.", "error")
            return redirect(url_for("reseller.index"))
        margin = _money(margin)
        price = _money(
            offer.wholesale_price * (Decimal("1") + margin / Decimal("100"))
        )
    elif field == "price":
        price = _decimal(request.form.get("resale_price", ""))
        if price is None or price < offer.wholesale_price:
            flash("El precio de reventa no puede ser menor al precio mayorista.", "error")
            return redirect(url_for("reseller.index"))
        price = _money(price)
        margin = _money(
            (price - offer.wholesale_price)
            / offer.wholesale_price
            * Decimal("100")
        )
    else:
        abort(400)

    if pricing is None:
        pricing = ResellerPricing(
            user_id=user_id,
            product_id=product_id,
        )
        db.session.add(pricing)
    pricing.resale_price = price
    pricing.margin_percent = margin
    db.session.commit()
    flash("Tu precio y margen de reventa quedaron actualizados.", "success")
    return redirect(url_for("reseller.index"))
