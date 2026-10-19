import hmac
import secrets

from flask import request, session


CSRF_SESSION_KEY = "_form_csrf_token"


def get_csrf_token():
    token = session.get(CSRF_SESSION_KEY)
    if not isinstance(token, str):
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def validate_csrf_token():
    expected = session.get(CSRF_SESSION_KEY)
    submitted = request.form.get("_csrf_token", "")
    return (
        isinstance(expected, str)
        and bool(expected)
        and hmac.compare_digest(expected, submitted)
    )
