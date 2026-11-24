"""Autenticação por sessão de cookie e proteção CSRF."""
import hmac
import secrets
from functools import wraps

from flask import jsonify, redirect, request, session, url_for

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_CSRF_KEY = "csrf_token"


def current_user_id() -> int | None:
    return session.get("user_id")


def get_csrf_token() -> str:
    token = session.get(_CSRF_KEY)
    if token is None:
        token = secrets.token_urlsafe(32)
        session[_CSRF_KEY] = token
    return token


def csrf_is_valid() -> bool:
    expected = session.get(_CSRF_KEY)
    sent = request.headers.get("X-CSRF-Token") or request.form.get(
        "csrf_token"
    )
    return bool(expected and sent) and hmac.compare_digest(expected, sent)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user_id() is None:
            if request.path.startswith("/api/"):
                return jsonify(error="Autenticação necessária."), 401
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapper
