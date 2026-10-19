import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from extensions import db
from models.inventory import Inventory
from models.product import Product
from models.reseller import ResellerOrder, ResellerPricing, ResellerStock
from models.user import User
from models.wallet import Wallet, WalletMovement, WalletTopUp
from models.wholesale import WholesaleOffer
from routes.payments import _apply_transaction, payments_bp
from routes.reseller import reseller_bp
from routes.sales import sales_bp
from routes.wallet import wallet_bp
from routes.dashboard import dashboard_bp
from routes.auth import auth_bp
from services.product_brands import get_product_brand


class ResellerFlowTests(unittest.TestCase):
    def setUp(self):
        template_directory = Path(__file__).resolve().parents[1] / "templates"
        self.app = Flask(
            __name__,
            template_folder=str(template_directory),
        )
        self.app.config.update(
            SECRET_KEY="reseller-test",
            SQLALCHEMY_DATABASE_URI="sqlite://",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            WOMPI_ENVIRONMENT="sandbox",
            WOMPI_PUBLIC_KEY="pub_test_example",
            WOMPI_PRIVATE_KEY="prv_test_example",
            WOMPI_INTEGRITY_SECRET="test_integrity_example",
            WOMPI_EVENTS_SECRET="test_events_example",
        )
        self.app.context_processor(
            lambda: {
                "music_tracks": [],
                "product_brand": get_product_brand,
            }
        )
        db.init_app(self.app)
        self.app.register_blueprint(reseller_bp)
        self.app.register_blueprint(sales_bp)
        self.app.register_blueprint(dashboard_bp)
        self.app.register_blueprint(auth_bp)
        self.app.register_blueprint(wallet_bp)
        self.app.register_blueprint(payments_bp)

        with self.app.app_context():
            db.create_all()
            user = User(
                name="Revendedor",
                username="revendedor",
                password_hash="unused",
                role="reseller",
                active=True,
            )
            product = Product(
                name="Netflix",
                duration_days=30,
                sale_price=Decimal("20000"),
                cost_price=Decimal("5000"),
                active=True,
            )
            db.session.add_all([user, product])
            db.session.flush()
            db.session.add_all(
                [
                    Wallet(user_id=user.id, balance=Decimal("50000")),
                    WholesaleOffer(
                        product_id=product.id,
                        wholesale_price=Decimal("10000"),
                        suggested_margin_percent=Decimal("40"),
                    ),
                    Inventory(
                        product_id=product.id,
                        reference="INV-000001",
                        status="available",
                    ),
                ]
            )
            db.session.commit()
            self.user_id = user.id
            self.product_id = product.id

        self.client = self.app.test_client()
        with self.client.session_transaction() as user_session:
            user_session["user_id"] = self.user_id
            user_session["role"] = "reseller"
            user_session["_form_csrf_token"] = "test-token"

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_purchase_debits_wallet_and_assigns_available_inventory(self):
        response = self.client.post(
            "/reseller/buy",
            data={
                "_csrf_token": "test-token",
                "product_id": str(self.product_id),
                "quantity": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            wallet = Wallet.query.filter_by(user_id=self.user_id).one()
            self.assertEqual(wallet.balance, Decimal("40000.00"))
            self.assertEqual(ResellerOrder.query.count(), 1)
            self.assertEqual(ResellerStock.query.count(), 1)
            self.assertEqual(
                Inventory.query.one().status,
                "assigned",
            )
            movement = WalletMovement.query.one()
            self.assertEqual(movement.amount, Decimal("-10000.00"))
            self.assertEqual(movement.movement_type, "wholesale_purchase")

    def test_verified_topup_credits_wallet_only_once(self):
        with self.app.app_context():
            topup = WalletTopUp(
                user_id=self.user_id,
                amount=Decimal("10000"),
                status="pending",
                reference="WT-idempotent-test",
            )
            db.session.add(topup)
            db.session.commit()
            transaction = {
                "reference": topup.reference,
                "amount_in_cents": 1_000_000,
                "currency": "COP",
                "payment_method_type": "PSE",
                "status": "APPROVED",
            }

            self.assertEqual(_apply_transaction(transaction), "APPROVED")
            self.assertEqual(_apply_transaction(transaction), "APPROVED")

            wallet = Wallet.query.filter_by(user_id=self.user_id).one()
            self.assertEqual(wallet.balance, Decimal("60000.00"))
            self.assertEqual(WalletMovement.query.count(), 1)
            self.assertEqual(
                WalletTopUp.query.one().status,
                "verified",
            )

    def test_wallet_rejects_below_minimum_and_accepts_minimum(self):
        under_minimum = self.client.post(
            "/wallet/",
            data={"_csrf_token": "test-token", "amount": "9999"},
        )
        self.assertEqual(under_minimum.status_code, 302)
        with self.app.app_context():
            self.assertEqual(WalletTopUp.query.count(), 0)

        minimum = self.client.post(
            "/wallet/",
            data={"_csrf_token": "test-token", "amount": "10000"},
        )
        self.assertEqual(minimum.status_code, 302)
        self.assertIn("/payments/wallet/", minimum.headers["Location"])
        with self.app.app_context():
            topup = WalletTopUp.query.one()
            self.assertEqual(topup.amount, Decimal("10000"))
            self.assertEqual(topup.status, "created")

    def test_topup_checkout_starts_a_pse_transaction(self):
        with self.app.app_context():
            topup = WalletTopUp(
                user_id=self.user_id,
                amount=Decimal("10000"),
                status="created",
                reference="WT-checkout-test",
            )
            db.session.add(topup)
            db.session.commit()
            topup_id = topup.id

        checkout_info = {
            "acceptance_token": "terms-token",
            "acceptance_url": "https://wompi.example/terms",
            "personal_data_token": "privacy-token",
            "personal_data_url": "https://wompi.example/privacy",
            "banks": [{"code": "001", "name": "Banco de prueba"}],
        }
        with (
            patch(
                "routes.payments.get_checkout_information",
                return_value=checkout_info,
            ),
            patch(
                "routes.payments.create_pse_transaction_for_amount",
                return_value=("https://bank.example/pse", {}),
            ) as create_transaction,
        ):
            checkout_page = self.client.get(
                f"/payments/wallet/{topup_id}/pse"
            )
            self.assertEqual(checkout_page.status_code, 200)
            self.assertIn(b"Recarga de saldo", checkout_page.data)

            response = self.client.post(
                f"/payments/wallet/{topup_id}/pse",
                data={
                    "_csrf_token": "test-token",
                    "full_name": "Comprador Ejemplo",
                    "email": "buyer@example.com",
                    "phone_number": "3001234567",
                    "user_type": "0",
                    "legal_id_type": "CC",
                    "legal_id": "12345678",
                    "financial_institution_code": "001",
                    "accept_terms": "yes",
                    "accept_personal_data": "yes",
                    "acceptance_token": "terms-token",
                    "personal_data_token": "privacy-token",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "https://bank.example/pse")
        self.assertEqual(create_transaction.call_args.args[0], Decimal("10000"))
        self.assertIn("topup_id=", create_transaction.call_args.args[3]["redirect_url"])
        with self.app.app_context():
            self.assertEqual(WalletTopUp.query.one().status, "pending")

    def test_price_and_margin_can_be_changed_by_reseller(self):
        response = self.client.post(
            f"/reseller/pricing/{self.product_id}",
            data={
                "_csrf_token": "test-token",
                "pricing_field": "price",
                "resale_price": "15000",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            pricing = ResellerPricing.query.one()
            self.assertEqual(pricing.resale_price, Decimal("15000.00"))
            self.assertEqual(pricing.margin_percent, Decimal("50.00"))

    def test_reseller_page_renders_recommendation_and_stock(self):
        response = self.client.get("/reseller/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"40.00%", response.data)
        self.assertIn(b"$14,000 COP", response.data)
        self.assertIn(b"product-brand-logo", response.data)
        self.assertIn(b"netflix.com", response.data)

    def test_sales_page_displays_brand_logo_in_product_catalog(self):
        with self.client.session_transaction() as user_session:
            user_session["role"] = "seller"

        response = self.client.get("/sales/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Elige el servicio", response.data)
        self.assertIn(b"Netflix", response.data)
        self.assertIn(b"netflix.com", response.data)

    def test_reseller_is_kept_out_of_global_sales_dashboard(self):
        self.assertEqual(self.client.get("/sales/").headers["Location"], "/reseller/")
        self.assertEqual(self.client.get("/").headers["Location"], "/reseller/")

    def test_new_registrations_receive_reseller_role(self):
        response = self.client.post(
            "/register",
            data={
                "name": "Nueva cuenta",
                "username": "nueva-cuenta",
                "password": "StrongPass123",
                "password_confirmation": "StrongPass123",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(
                User.query.filter_by(username="nueva-cuenta").one().role,
                "reseller",
            )


if __name__ == "__main__":
    unittest.main()
