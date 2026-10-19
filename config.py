import os
import secrets

from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///stream_panel.db"
    )

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql+psycopg://",
            1
        )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WOMPI_ENVIRONMENT = os.getenv(
        "WOMPI_ENVIRONMENT",
        "sandbox"
    ).strip().lower()

    WOMPI_PUBLIC_KEY = os.getenv(
        "WOMPI_PUBLIC_KEY",
        ""
    ).strip()

    WOMPI_PRIVATE_KEY = os.getenv(
        "WOMPI_PRIVATE_KEY",
        ""
    ).strip()

    WOMPI_INTEGRITY_SECRET = os.getenv(
        "WOMPI_INTEGRITY_SECRET",
        ""
    ).strip()

    WOMPI_EVENTS_SECRET = os.getenv(
        "WOMPI_EVENTS_SECRET",
        ""
    ).strip()

    WOMPI_REDIRECT_URL = os.getenv(
        "WOMPI_REDIRECT_URL",
        ""
    ).strip()
