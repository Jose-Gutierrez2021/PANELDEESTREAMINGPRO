from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from extensions import db


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        nullable=False,
        default="seller"
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256",
            salt_length=16
        )

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )
