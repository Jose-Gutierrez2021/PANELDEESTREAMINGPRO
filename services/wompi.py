import hashlib
import hmac
import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from flask import current_app


logger = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 15


class WompiError(Exception):
    pass


class WompiNotConfiguredError(WompiError):
    pass


def is_configured():
    config = current_app.config
    environment = config.get("WOMPI_ENVIRONMENT")
    public_key = config.get("WOMPI_PUBLIC_KEY", "")
    private_key = config.get("WOMPI_PRIVATE_KEY", "")
    integrity_secret = config.get("WOMPI_INTEGRITY_SECRET", "")
    events_secret = config.get("WOMPI_EVENTS_SECRET", "")

    if environment == "sandbox":
        prefixes = ("pub_test_", "prv_test_", "test_integrity_", "test_events_")
    elif environment == "production":
        prefixes = ("pub_prod_", "prv_prod_", "prod_integrity_", "prod_events_")
    else:
        return False

    values = (public_key, private_key, integrity_secret, events_secret)
    return all(
        value.startswith(prefix)
        for value, prefix in zip(values, prefixes)
    )


def _require_configured():
    if not is_configured():
        raise WompiNotConfiguredError(
            "Wompi no está configurado con llaves válidas para el ambiente seleccionado."
        )

    if current_app.config["WOMPI_ENVIRONMENT"] == "production":
        return "https://production.wompi.co/v1"
    return "https://sandbox.wompi.co/v1"


def _api_request(method, path, *, data=None, headers=None, authenticated=False):
    base_url = _require_configured()
    request_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if headers:
        request_headers.update(headers)
    if authenticated:
        request_headers["Authorization"] = (
            f"Bearer {current_app.config['WOMPI_PRIVATE_KEY']}"
        )

    body = None if data is None else json.dumps(data).encode("utf-8")
    request = Request(
        f"{base_url}{path}",
        data=body,
        headers=request_headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        logger.warning("Wompi API returned HTTP %s for %s.", error.code, path)
        raise WompiError(
            "Wompi no pudo procesar la solicitud. Intenta de nuevo más tarde."
        ) from error
    except URLError as error:
        logger.warning("Wompi API request failed for %s: %s.", path, error.reason)
        raise WompiError(
            "No fue posible conectar con Wompi. Intenta de nuevo más tarde."
        ) from error
    except TimeoutError as error:
        logger.warning("Wompi API request timed out for %s.", path)
        raise WompiError(
            "Wompi tardó demasiado en responder. Intenta de nuevo más tarde."
        ) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        logger.warning("Wompi API returned an invalid response for %s.", path)
        raise WompiError(
            "Wompi devolvió una respuesta no válida."
        ) from error

    if not isinstance(payload, dict):
        raise WompiError("Wompi devolvió una respuesta no válida.")
    return payload


def _response_data(response):
    data = response.get("data")
    if not isinstance(data, dict):
        raise WompiError("Wompi devolvió una respuesta incompleta.")
    return data


def build_integrity_signature(reference, amount_in_cents):
    integrity_secret = current_app.config["WOMPI_INTEGRITY_SECRET"]
    signed_value = f"{reference}{amount_in_cents}COP{integrity_secret}"
    return hashlib.sha256(signed_value.encode("utf-8")).hexdigest()


def get_checkout_information():
    public_key = current_app.config["WOMPI_PUBLIC_KEY"]
    merchant_response = _api_request(
        "GET",
        "/merchants/info",
        headers={"x-merchant-public-key": public_key},
    )
    merchant = _response_data(merchant_response)

    acceptance = merchant.get("presigned_acceptance") or merchant.get("acceptance")
    personal_data = (
        merchant.get("presigned_personal_data_auth")
        or merchant.get("personal_data_auth")
    )
    if (
        not isinstance(acceptance, dict)
        or not isinstance(personal_data, dict)
        or not acceptance.get("acceptance_token")
        or not personal_data.get("acceptance_token")
    ):
        raise WompiError(
            "Wompi no devolvió los documentos de aceptación requeridos."
        )

    banks_response = _api_request(
        "GET",
        "/pse/financial_institutions",
        headers={
            "Authorization": f"Bearer {public_key}",
        },
    )
    banks = banks_response.get("data")
    if not isinstance(banks, list):
        raise WompiError("Wompi no devolvió la lista de bancos PSE.")

    normalized_banks = []
    for bank in banks:
        if not isinstance(bank, dict):
            continue
        code = bank.get("financial_institution_code", bank.get("code"))
        name = bank.get("financial_institution_name", bank.get("name"))
        if code is not None and isinstance(name, str) and name.strip():
            normalized_banks.append({"code": str(code), "name": name.strip()})

    return {
        "acceptance_token": acceptance.get("acceptance_token"),
        "acceptance_url": acceptance.get("permalink"),
        "personal_data_token": personal_data.get("acceptance_token"),
        "personal_data_url": personal_data.get("permalink"),
        "banks": sorted(normalized_banks, key=lambda bank: bank["name"].casefold()),
    }


def create_pse_transaction(sale, payment, payer, acceptance_token, personal_data_token):
    return create_pse_transaction_for_amount(
        sale.price,
        payment.reference,
        f"Pago StreamPanel venta {sale.id}",
        payer,
        acceptance_token,
        personal_data_token,
    )


def create_pse_transaction_for_amount(
    amount,
    reference,
    description,
    payer,
    acceptance_token,
    personal_data_token,
):
    _require_configured()
    amount_in_cents = int(amount * 100)
    signature = build_integrity_signature(reference, amount_in_cents)

    transaction = {
        "acceptance_token": acceptance_token,
        "accept_personal_auth": personal_data_token,
        "amount_in_cents": amount_in_cents,
        "currency": "COP",
        "customer_email": payer["email"],
        "full_name": payer["full_name"],
        "phone_number": payer["phone_number"],
        "reference": reference,
        "signature": signature,
        "redirect_url": payer["redirect_url"],
        "payment_method": {
            "type": "PSE",
            "user_type": int(payer["user_type"]),
            "user_legal_id_type": payer["legal_id_type"],
            "user_legal_id": payer["legal_id"],
            "financial_institution_code": payer["financial_institution_code"],
            "payment_description": description[:64],
        },
    }
    response = _api_request(
        "POST",
        "/transactions",
        data=transaction,
        authenticated=True,
    )
    result = _response_data(response)
    transaction_id = result.get("id")
    if not isinstance(transaction_id, str) or not transaction_id:
        raise WompiError("Wompi no devolvió el identificador de la transacción.")

    for attempt in range(5):
        payment_method = result.get("payment_method")
        extra = payment_method.get("extra") if isinstance(payment_method, dict) else None
        payment_url = extra.get("async_payment_url") if isinstance(extra, dict) else None
        if isinstance(payment_url, str) and payment_url.startswith("https://"):
            return payment_url, result
        if attempt < 4:
            time.sleep(1)
            result = get_transaction(transaction_id)

    raise WompiError(
        "Wompi aún no habilita el enlace bancario PSE. "
        "Intenta abrir el pago de nuevo en unos minutos."
    )


def get_transaction(transaction_id):
    escaped_id = quote(str(transaction_id), safe="")
    response = _api_request(
        "GET",
        f"/transactions/{escaped_id}",
        authenticated=True,
    )
    return _response_data(response)


def verify_event_signature(payload, header_checksum=None):
    if not is_configured():
        return False

    signature = payload.get("signature")
    if not isinstance(signature, dict):
        return False

    properties = signature.get("properties")
    data = payload.get("data")
    timestamp = payload.get("timestamp")
    checksum = header_checksum or signature.get("checksum")
    if (
        not isinstance(properties, list)
        or not properties
        or not isinstance(data, dict)
        or timestamp is None
        or not isinstance(checksum, str)
    ):
        return False

    values = []
    for property_path in properties:
        if not isinstance(property_path, str):
            return False
        value = data
        for part in property_path.split("."):
            if not isinstance(value, dict) or part not in value:
                return False
            value = value[part]
        if value is None:
            return False
        values.append(str(value))

    signed_payload = "".join(values) + str(timestamp)
    signed_payload += current_app.config["WOMPI_EVENTS_SECRET"]
    expected_checksum = hashlib.sha256(
        signed_payload.encode("utf-8")
    ).hexdigest()
    return hmac.compare_digest(expected_checksum.lower(), checksum.lower())
