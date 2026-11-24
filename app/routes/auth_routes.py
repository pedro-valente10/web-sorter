"""Páginas de cadastro, login e logout (adaptador HTTP -> casos de uso)."""
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.container import get_container
from app.security import current_user_id, get_csrf_token
from domain.errors import DomainError, UsernameAlreadyExistsError

bp = Blueprint("auth", __name__)


@bp.get("/register")
def register_page():
    if current_user_id() is not None:
        return redirect(url_for("sorter.index"))
    return render_template("register.html")


@bp.post("/register")
def register():
    form = request.form
    try:
        get_container().register_user.execute(
            form.get("username", ""), form.get("password", "")
        )
    except DomainError as error:
        status = 409 if isinstance(error, UsernameAlreadyExistsError) else 400
        return render_template("register.html", error=str(error)), status
    flash("Conta criada! Entre com seus dados.")
    return redirect(url_for("auth.login"))


@bp.get("/login")
def login_page():
    if current_user_id() is not None:
        return redirect(url_for("sorter.index"))
    return render_template("login.html")


@bp.post("/login")
def login():
    form = request.form
    try:
        user = get_container().authenticate_user.execute(
            form.get("username", ""), form.get("password", "")
        )
    except DomainError as error:
        return render_template("login.html", error=str(error)), 401
    session.clear()  # evita fixação de sessão
    session["user_id"] = user.id
    session["username"] = user.username
    get_csrf_token()
    return redirect(url_for("sorter.index"))


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
