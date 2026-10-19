import logging
import re
import secrets

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from extensions import db
from models.payment import Payment
from models.sale import Sale
from models.wallet import Wallet, WalletMovement, WalletTopUp
from services.security import get_csrf_token, validate_csrf_token
from services.wompi import (
    WompiError,
    create_pse_transaction,
    create_pse_transaction_for_amount,
    get_checkout_information,
    get_transaction,
    is_configured,
    verify_event_signature,
)


logger = logging.getLogger(__name__)

payments_bp = Blueprint(
    "payments",
    __name__,
    url_prefix="/payments"
)


def _payer_from_form(checkout_info):
    payer = {
        "email": request.form.get("email", "").strip(),
        "full_name": request.form.get("full_name", "").strip(),
        "phone_number": re.sub(
            r"\D",
            "",
            request.form.get("phone_number", ""),
        ),
        "user_type": request.form.get("user_type", ""),
        "legal_id_type": request.form.get("legal_id_type", "").strip(),
        "legal_id": re.sub(
            r"[^A-Za-z0-9]",
            "",
            request.form.get("legal_id", ""),
        ),
        "financial_institution_code": request.form.get(
            "financial_institution_code",
            "",
        ).strip(),
        "redirect_url": current_app.config.get("WOMPI_REDIRECT_URL")
        or url_for("payments.result", _external=True),
    }
    if len(payer["phone_number"]) == 10:
        payer["phone_number"] = f"57{payer['phone_number']}"

    accepted_legal_ids = {"CC", "CE", "NIT", "PP", "TI", "DNI", "OTHER"}
    available_bank_codes = {
        bank["code"]
        for bank in checkout_info["banks"]
    }
    valid_phone = (
        len(payer["phone_number"]) == 10
        and payer["phone_number"].startswith("3")
    ) or (
        len(payer["phone_number"]) == 12
        and payer["phone_number"].startswith("57")
    )
    if (
        not payer["full_name"]
        or len(payer["full_name"]) > 100
        or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", payer["email"])
        or len(payer["email"]) > 254
        or not valid_phone
        or payer["user_type"] not in {"0", "1"}
        or payer["legal_id_type"] not in accepted_legal_ids
        or not payer["legal_id"].isalnum()
        or not 5 <= len(payer["legal_id"]) <= 20
        or payer["financial_institution_code"] not in available_bank_codes
        or request.form.get("accept_terms") != "yes"
        or request.form.get("accept_personal_data") != "yes"
        or request.form.get("acceptance_token")
        != checkout_info["acceptance_token"]
        or request.form.get("personal_data_token")
        != checkout_info["personal_data_token"]
    ):
        return None
    return payer


def _apply_transaction(transaction):
    reference = transaction.get("reference")
    if not isinstance(reference, str):
        logger.warning("Wompi transaction has no merchant reference.")
        return "unknown"

    payment = Payment.query.filter_by(reference=reference).first()
    topup = None
    if payment is None:
        topup = WalletTopUp.query.filter_by(reference=reference).with_for_update().first()
    if payment is None and topup is None:
        logger.warning("Wompi transaction reference was not found.")
        return "unknown"

    expected_payment = payment if payment is not None else topup
    amount_in_cents = transaction.get("amount_in_cents")
    try:
        transaction_amount = int(amount_in_cents)
        expected_amount = int(expected_payment.amount * 100)
    except (TypeError, ValueError, OverflowError):
        logger.warning("Wompi transaction has an invalid amount.")
        return "invalid"

    if (
        transaction_amount != expected_amount
        or transaction.get("currency") != "COP"
        or transaction.get("payment_method_type") != "PSE"
    ):
        logger.warning(
            "Wompi transaction does not match payment %s.",
            expected_payment.id,
        )
        return "invalid"

    status = transaction.get("status")
    if topup is not None:
        if status == "APPROVED":
            if topup.status != "verified":
                wallet = Wallet.query.filter_by(user_id=topup.user_id).with_for_update().first()
                if wallet is None:
                    wallet = Wallet(user_id=topup.user_id, balance=0)
                    db.session.add(wallet)
                    db.session.flush()
                wallet.balance += topup.amount
                db.session.add(
                    WalletMovement(
                        user_id=topup.user_id,
                        amount=topup.amount,
                        movement_type="pse_topup",
                        topup_id=topup.id,
                    )
                )
            topup.status = "verified"
        elif status in {"DECLINED", "ERROR", "VOIDED"}:
            if topup.status != "verified":
                topup.status = "rejected"
        elif topup.status != "verified":
            topup.status = "pending"
    else:
        sale = payment.sale
        if status == "APPROVED":
            payment.status = "verified"
            sale.payment_status = "verified"
        elif status in {"DECLINED", "ERROR", "VOIDED"}:
            payment.status = "rejected"
            if sale.payment_status != "verified":
                sale.payment_status = "rejected"
        else:
            payment.status = "pending"
            if sale.payment_status != "verified":
                sale.payment_status = "pending"

    db.session.commit()
    return status or "pending"


@payments_bp.route(
    "/<int:sale_id>/pse",
    methods=["GET", "POST"]
)
def pse_checkout(sale_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("role") not in {"admin", "seller"}:
        abort(403)

    sale = Sale.query.get_or_404(sale_id)
    if sale.payment_status == "verified":
        flash("Esta venta ya tiene el pago confirmado.", "info")
        return redirect(url_for("sales.index"))

    active_payment = Payment.query.filter_by(
        sale_id=sale.id,
        status="pending",
    ).first()
    if request.method == "POST" and active_payment:
        flash(
            "Esta venta ya tiene un pago PSE en proceso. "
            "Espera la respuesta del banco antes de reintentar.",
            "info",
        )
        return redirect(url_for("sales.index"))

    if active_payment:
        checkout_info = None
        checkout_error = None
    elif not is_configured():
        checkout_info = None
        checkout_error = (
            "Los pagos PSE todavía no están disponibles. "
            "Configura las llaves de Wompi para continuar."
        )
    else:
        try:
            checkout_info = get_checkout_information()
            checkout_error = None
        except WompiError as error:
            current_app.logger.warning(
                "Could not load Wompi checkout information: %s",
                error,
            )
            checkout_info = None
            checkout_error = str(error)

    if request.method == "GET":
        return render_template(
            "payments/pse_checkout.html",
            sale=sale,
            order_title=f"VENTA #{sale.id}",
            order_reference=sale.id,
            order_name=sale.product.name,
            order_amount=sale.price,
            checkout_action=url_for(
                "payments.pse_checkout",
                sale_id=sale.id,
            ),
            checkout_back_url=url_for("sales.index"),
            checkout_title="Completa tu pago PSE",
            checkout_intro=(
                "Selecciona el banco del pagador. Wompi procesará el pago y lo enviará "
                "a la cuenta bancaria del comercio."
            ),
            checkout_info=checkout_info,
            checkout_error=checkout_error,
            active_payment=active_payment,
            csrf_token=get_csrf_token(),
        )

    if not validate_csrf_token():
        abort(400)

    if checkout_error or checkout_info is None:
        flash(checkout_error or "Wompi no está disponible.", "error")
        return redirect(url_for("sales.index"))

    payer = _payer_from_form(checkout_info)
    if payer is None:
        flash(
            "Revisa los datos del titular, el banco y las dos autorizaciones requeridas.",
            "error",
        )
        return redirect(url_for("payments.pse_checkout", sale_id=sale.id))

    if (
        current_app.config["WOMPI_ENVIRONMENT"] == "production"
        and not payer["redirect_url"].startswith("https://")
    ):
        flash(
            "Configura WOMPI_REDIRECT_URL con la dirección HTTPS pública "
            "de este sitio antes de habilitar pagos reales.",
            "error",
        )
        return redirect(url_for("payments.pse_checkout", sale_id=sale.id))

    payment = Payment(
        sale_id=sale.id,
        amount=sale.price,
        method="PSE",
        reference=f"SP{sale.id}-{secrets.token_hex(8)}",
        status="pending",
    )
    sale.payment_method = "PSE"
    sale.payment_status = "pending"
    db.session.add(payment)
    db.session.commit()

    try:
        if not checkout_info["acceptance_url"] or not checkout_info["personal_data_url"]:
            raise WompiError(
                "Wompi no devolvió los documentos de aceptación requeridos."
            )
        payment_url, _ = create_pse_transaction(
            sale,
            payment,
            payer,
            checkout_info["acceptance_token"],
            checkout_info["personal_data_token"],
        )
    except WompiError as error:
        current_app.logger.warning(
            "Could not start Wompi PSE payment for sale %s: %s",
            sale.id,
            error,
        )
        payment.status = "initiation_error"
        db.session.commit()
        flash(str(error), "error")
        return redirect(url_for("sales.index"))

    return redirect(payment_url)


@payments_bp.route(
    "/wallet/<int:topup_id>/pse",
    methods=["GET", "POST"],
)
def topup_pse_checkout(topup_id):
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("auth.login"))
    if session.get("role") == "admin":
        abort(403)

    topup = WalletTopUp.query.filter_by(
        id=topup_id,
        user_id=user_id,
    ).first_or_404()
    if topup.status not in {"created", "initiation_error"}:
        return render_template(
            "payments/pse_checkout.html",
            order_title="Recarga de saldo",
            order_reference=topup.id,
            order_name="Saldo de cartera",
            order_amount=topup.amount,
            checkout_action=url_for(
                "payments.topup_pse_checkout",
                topup_id=topup.id,
            ),
            checkout_back_url=url_for("wallet.index"),
            checkout_title="Completa tu recarga por PSE",
            checkout_intro="La recarga se abonará a tu saldo cuando Wompi confirme el pago.",
            checkout_info=None,
            checkout_error=None,
            active_payment=topup,
            csrf_token=get_csrf_token(),
        )

    if not is_configured():
        checkout_info = None
        checkout_error = (
            "Los pagos PSE todavía no están disponibles. "
            "Configura las llaves de Wompi para continuar."
        )
    else:
        try:
            checkout_info = get_checkout_information()
            checkout_error = None
        except WompiError as error:
            current_app.logger.warning(
                "Could not load Wompi checkout information for wallet top-up: %s",
                error,
            )
            checkout_info = None
            checkout_error = str(error)

    context = {
        "order_title": "Recarga de saldo",
        "order_reference": topup.id,
        "order_name": "Saldo de cartera",
        "order_amount": topup.amount,
        "checkout_action": url_for(
            "payments.topup_pse_checkout",
            topup_id=topup.id,
        ),
        "checkout_back_url": url_for("wallet.index"),
        "checkout_title": "Completa tu recarga por PSE",
        "checkout_intro": "La recarga se abonará a tu saldo cuando Wompi confirme el pago.",
        "checkout_info": checkout_info,
        "checkout_error": checkout_error,
        "active_payment": None,
        "csrf_token": get_csrf_token(),
    }
    if request.method == "GET":
        return render_template("payments/pse_checkout.html", **context)
    if not validate_csrf_token():
        abort(400)
    if checkout_error or checkout_info is None:
        flash(checkout_error or "Wompi no está disponible.", "error")
        return redirect(url_for("wallet.index"))

    payer = _payer_from_form(checkout_info)
    if payer is None:
        flash(
            "Revisa los datos del titular, el banco y las dos autorizaciones requeridas.",
            "error",
        )
        return redirect(url_for("payments.topup_pse_checkout", topup_id=topup.id))
    if (
        current_app.config["WOMPI_ENVIRONMENT"] == "production"
        and not payer["redirect_url"].startswith("https://")
    ):
        flash(
            "Configura WOMPI_REDIRECT_URL con la dirección HTTPS pública "
            "de este sitio antes de habilitar pagos reales.",
            "error",
        )
        return redirect(url_for("wallet.index"))

    topup.status = "pending"
    topup.reference = f"WT{topup.id}-{secrets.token_hex(8)}"
    db.session.commit()
    query_separator = "&" if "?" in payer["redirect_url"] else "?"
    payer["redirect_url"] = (
        f"{payer['redirect_url']}{query_separator}topup_id={topup.id}"
    )
    try:
        if not checkout_info["acceptance_url"] or not checkout_info["personal_data_url"]:
            raise WompiError(
                "Wompi no devolvió los documentos de aceptación requeridos."
            )
        payment_url, _ = create_pse_transaction_for_amount(
            topup.amount,
            topup.reference,
            f"Recarga StreamPanel {topup.id}",
            payer,
            checkout_info["acceptance_token"],
            checkout_info["personal_data_token"],
        )
    except WompiError as error:
        current_app.logger.warning(
            "Could not start Wompi PSE wallet top-up %s: %s",
            topup.id,
            error,
        )
        if topup.status != "verified":
            topup.status = "initiation_error"
            db.session.commit()
        flash(str(error), "error")
        return redirect(url_for("wallet.index"))

    return redirect(payment_url)


@payments_bp.route(
    "/wompi/result",
    methods=["GET"]
)
def result():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    topup_id = request.args.get("topup_id", "").strip()
    if topup_id.isdigit():
        topup = WalletTopUp.query.filter_by(
            id=int(topup_id),
            user_id=session["user_id"],
        ).first()
        if topup is None:
            abort(404)
        return_endpoint = "wallet.index"
    elif session.get("role") in {"admin", "seller"}:
        return_endpoint = "sales.index"
    else:
        return redirect(url_for("wallet.index"))
    transaction_id = request.args.get("id", "").strip()
    if not transaction_id:
        flash(
            "Wompi devolvió al sitio sin un identificador de transacción. "
            "El estado se actualizará al recibir la notificación del pago.",
            "info",
        )
        return redirect(url_for(return_endpoint))

    try:
        transaction = get_transaction(transaction_id)
    except WompiError as error:
        current_app.logger.warning(
            "Could not verify returned Wompi transaction: %s",
            error,
        )
        flash(
            "No se pudo consultar el estado con Wompi. "
            "La confirmación se actualizará al recibir su notificación.",
            "info",
        )
        return redirect(url_for(return_endpoint))

    if transaction.get("id") != transaction_id:
        current_app.logger.warning(
            "Wompi returned a different transaction ID than requested."
        )
        flash(
            "No se pudo validar la respuesta del proveedor de pagos.",
            "error",
        )
        return redirect(url_for(return_endpoint))

    status = _apply_transaction(transaction)
    if status == "APPROVED":
        flash("Pago PSE confirmado.", "success")
    elif status in {"DECLINED", "ERROR", "VOIDED"}:
        flash(
            "Wompi no aprobó el pago. Puedes intentar de nuevo por PSE.",
            "error",
        )
    elif status in {"unknown", "invalid"}:
        flash(
            "No se pudo asociar la respuesta de Wompi con esta venta. "
            "El pago no se marcó como confirmado.",
            "error",
        )
    else:
        flash(
            "El pago sigue pendiente de confirmación del banco.",
            "info",
        )
    return redirect(url_for(return_endpoint))


@payments_bp.route(
    "/wompi/webhook",
    methods=["POST"]
)
def webhook():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        abort(400)
    if payload.get("event") != "transaction.updated":
        return "", 200

    if not verify_event_signature(
        payload,
        request.headers.get("X-Event-Checksum"),
    ):
        current_app.logger.warning("Rejected Wompi event with invalid signature.")
        abort(400)

    event_data = payload.get("data")
    transaction_data = (
        event_data.get("transaction")
        if isinstance(event_data, dict)
        else None
    )
    transaction_id = (
        transaction_data.get("id")
        if isinstance(transaction_data, dict)
        else None
    )
    if not transaction_id:
        abort(400)

    try:
        transaction = get_transaction(transaction_id)
    except WompiError:
        current_app.logger.exception(
            "Could not retrieve Wompi transaction %s from its webhook.",
            transaction_id,
        )
        return "Could not verify transaction with Wompi.", 503

    if str(transaction.get("id", "")) != str(transaction_id):
        current_app.logger.warning(
            "Wompi webhook transaction ID did not match the API response."
        )
        return "Transaction ID does not match.", 400

    result_status = _apply_transaction(transaction)
    if result_status == "invalid":
        return "Transaction does not match the pending payment.", 400
    return "", 200
