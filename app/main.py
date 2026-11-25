"""Ponto de entrada: monta o Flask e liga as camadas.

Executar:  python -m app.main   (abre em http://127.0.0.1:5000)
"""
from flask import Flask, jsonify, request

from app.config import Config
from app.container import build_container
from app.routes import auth_routes, batch_routes, sorter_routes
from app.security import SAFE_METHODS, csrf_is_valid, get_csrf_token
from domain.errors import (
    DomainError,
    InvalidCredentialsError,
    NotFoundError,
    UsernameAlreadyExistsError,
    ValidationError,
)
from infra.db.database import Database

_STATUS_BY_ERROR = (
    (ValidationError, 400),
    (NotFoundError, 404),
    (UsernameAlreadyExistsError, 409),
    (InvalidCredentialsError, 401),
)

# Só nomes de arquivos trafegam; 16 MB cabem pastas muito grandes.
_MAX_BODY_BYTES = 16 * 1024 * 1024

_CSP = (
    "default-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:; "
    "style-src 'self'; script-src 'self'; frame-ancestors 'none'"
)


def create_app(config: Config | None = None) -> Flask:
    config = config or Config.from_env()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=config.secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=_MAX_BODY_BYTES,
    )

    database = Database(config.database_path)
    database.init_schema()
    app.extensions["container"] = build_container(database)

    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(sorter_routes.bp)
    app.register_blueprint(batch_routes.bp)
    app.context_processor(lambda: {"csrf_token": get_csrf_token})

    @app.before_request
    def protect_against_csrf():
        if request.method not in SAFE_METHODS and not csrf_is_valid():
            return jsonify(error="Token CSRF inválido."), 400

    @app.after_request
    def add_security_headers(response):
        response.headers["Content-Security-Policy"] = _CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @app.errorhandler(DomainError)
    def handle_domain_error(error):
        status = next(
            (code for kind, code in _STATUS_BY_ERROR
             if isinstance(error, kind)),
            400,
        )
        return jsonify(error=str(error)), status

    return app


def main() -> None:
    create_app().run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
