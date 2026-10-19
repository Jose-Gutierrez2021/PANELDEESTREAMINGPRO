import hashlib
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask
from jinja2 import Environment, FileSystemLoader

from routes.payments import payments_bp
from routes.sales import sales_bp
from routes.wallet import wallet_bp
from services.security import CSRF_SESSION_KEY, validate_csrf_token
from services.wompi import (
    build_integrity_signature,
    create_pse_transaction,
    is_configured,
    verify_event_signature,
)


class WompiServiceTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            WOMPI_ENVIRONMENT="sandbox",
            WOMPI_PUBLIC_KEY="pub_test_example",
            WOMPI_PRIVATE_KEY="prv_test_example",
            WOMPI_INTEGRITY_SECRET="test_integrity_example",
            WOMPI_EVENTS_SECRET="test_events_example",
        )

    def test_sandbox_keys_are_required_and_must_match_environment(self):
        with self.app.app_context():
            self.assertTrue(is_configured())
            self.app.config["WOMPI_PRIVATE_KEY"] = "prv_prod_example"
            self.assertFalse(is_configured())

    def test_payment_routes_are_registered(self):
        app = Flask(__name__)
        app.register_blueprint(sales_bp)
        app.register_blueprint(payments_bp)
        app.register_blueprint(wallet_bp)
        rules = {rule.endpoint: rule.rule for rule in app.url_map.iter_rules()}
        self.assertEqual(rules["payments.pse_checkout"], "/payments/<int:sale_id>/pse")
        self.assertEqual(rules["payments.webhook"], "/payments/wompi/webhook")
        self.assertEqual(
            rules["payments.topup_pse_checkout"],
            "/payments/wallet/<int:topup_id>/pse",
        )

    def test_payment_templates_parse(self):
        template_directory = Path(__file__).resolve().parents[1] / "templates"
        templates = Environment(
            loader=FileSystemLoader(template_directory)
        )
        templates.get_template("sales/index.html")
        templates.get_template("payments/pse_checkout.html")
        templates.get_template("wallet/index.html")
        templates.get_template("reseller/index.html")
        templates.get_template("products/index.html")

    def test_csrf_token_must_match_the_session(self):
        self.app.secret_key = "unit-test-secret"
        with self.app.test_request_context(
            "/sales/",
            method="POST",
            data={"_csrf_token": "session-token"},
        ):
            from flask import session

            session[CSRF_SESSION_KEY] = "session-token"
            self.assertTrue(validate_csrf_token())
            session[CSRF_SESSION_KEY] = "different-token"
            self.assertFalse(validate_csrf_token())

    def test_integrity_signature_uses_reference_amount_currency_and_secret(self):
        with self.app.app_context():
            expected = hashlib.sha256(
                b"SP10abc12550COPtest_integrity_example"
            ).hexdigest()
            self.assertEqual(
                build_integrity_signature("SP10abc", 12550),
                expected,
            )

    def test_event_signature_detects_payload_changes(self):
        data = {
            "transaction": {
                "id": "wompi-123",
                "status": "APPROVED",
                "amount_in_cents": 12550,
            }
        }
        timestamp = 1_792_000_000
        signed_value = "wompi-123APPROVED12550"
        signed_value += str(timestamp) + "test_events_example"
        checksum = hashlib.sha256(signed_value.encode("utf-8")).hexdigest()
        payload = {
            "event": "transaction.updated",
            "timestamp": timestamp,
            "data": data,
            "signature": {
                "properties": [
                    "transaction.id",
                    "transaction.status",
                    "transaction.amount_in_cents",
                ],
                "checksum": checksum,
            },
        }

        with self.app.app_context():
            self.assertTrue(verify_event_signature(payload))
            payload["data"]["transaction"]["status"] = "DECLINED"
            self.assertFalse(verify_event_signature(payload))

    @patch("services.wompi._api_request")
    def test_creates_only_a_pse_transaction(self, api_request):
        api_request.return_value = {
            "data": {
                "id": "wompi-123",
                "payment_method": {
                    "extra": {
                        "async_payment_url": "https://bank.example/pse"
                    }
                },
            }
        }
        sale = SimpleNamespace(id=42, price=Decimal("125.50"))
        payment = SimpleNamespace(reference="SP42unique")
        payer = {
            "email": "buyer@example.com",
            "full_name": "Comprador Ejemplo",
            "phone_number": "573001234567",
            "user_type": "0",
            "legal_id_type": "CC",
            "legal_id": "12345678",
            "financial_institution_code": "1",
            "redirect_url": "https://example.com/payments/wompi/result",
        }

        with self.app.app_context():
            payment_url, _ = create_pse_transaction(
                sale,
                payment,
                payer,
                "acceptance",
                "personal-data",
            )

        self.assertEqual(payment_url, "https://bank.example/pse")
        request = api_request.call_args
        transaction = request.kwargs["data"]
        self.assertTrue(request.kwargs["authenticated"])
        self.assertEqual(request.args[1], "/transactions")
        self.assertEqual(transaction["amount_in_cents"], 12550)
        self.assertEqual(transaction["currency"], "COP")
        self.assertEqual(transaction["payment_method"]["type"], "PSE")
        self.assertEqual(
            transaction["payment_method"]["financial_institution_code"],
            "1",
        )


if __name__ == "__main__":
    unittest.main()
