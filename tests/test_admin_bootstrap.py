import unittest
from unittest.mock import patch

from app import create_app
from config import Config
from extensions import db
from models.user import User


class AdminBootstrapTests(unittest.TestCase):
    def test_bootstraps_admin_only_from_configured_credentials(self):
        with (
            patch.object(Config, "ADMIN_USERNAME", "first-admin"),
            patch.object(Config, "ADMIN_PASSWORD", "a-long-test-password"),
            patch.object(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://"),
        ):
            app = create_app()

        with app.app_context():
            admin = User.query.filter_by(username="first-admin").one()
            self.assertEqual(admin.role, "admin")
            self.assertTrue(admin.check_password("a-long-test-password"))
            self.assertIsNone(User.query.filter_by(username="admin").first())
            db.session.remove()

    def test_does_not_create_admin_without_credentials(self):
        with (
            patch.object(Config, "ADMIN_USERNAME", ""),
            patch.object(Config, "ADMIN_PASSWORD", ""),
            patch.object(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://"),
        ):
            app = create_app()

        with app.app_context():
            self.assertEqual(User.query.filter_by(role="admin").count(), 0)
            db.session.remove()

    def test_rejects_partial_or_short_admin_credentials(self):
        scenarios = [
            ("first-admin", ""),
            ("", "a-long-test-password"),
            ("first-admin", "too-short"),
        ]

        for username, password in scenarios:
            with self.subTest(username=username, password=password):
                with (
                    patch.object(Config, "ADMIN_USERNAME", username),
                    patch.object(Config, "ADMIN_PASSWORD", password),
                    patch.object(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://"),
                ):
                    with self.assertRaises(RuntimeError):
                        create_app()


if __name__ == "__main__":
    unittest.main()
