import unittest

from config import normalize_database_url


class DatabaseUrlTests(unittest.TestCase):
    def test_converts_postgres_scheme_to_installed_psycopg_driver(self):
        self.assertEqual(
            normalize_database_url("postgres://user:pass@host/db"),
            "postgresql+psycopg://user:pass@host/db",
        )

    def test_converts_postgresql_scheme_to_installed_psycopg_driver(self):
        self.assertEqual(
            normalize_database_url("postgresql://user:pass@host/db?sslmode=require"),
            "postgresql+psycopg://user:pass@host/db?sslmode=require",
        )

    def test_preserves_other_database_urls(self):
        self.assertEqual(
            normalize_database_url("sqlite:///stream_panel.db"),
            "sqlite:///stream_panel.db",
        )
        self.assertEqual(
            normalize_database_url(
                "postgresql+psycopg://user:pass@host/db"
            ),
            "postgresql+psycopg://user:pass@host/db",
        )


if __name__ == "__main__":
    unittest.main()
