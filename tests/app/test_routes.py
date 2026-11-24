"""Teste ponta a ponta: HTTP -> casos de uso -> SQLite real (arquivo temp)."""
import pytest

from app.config import Config
from app.main import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(
        Config(database_path=str(tmp_path / "t.db"), secret_key="teste")
    )


def csrf_of(client):
    with client.session_transaction() as flask_session:
        return flask_session["csrf_token"]


def register_and_login(client, username="ana", password="senha-segura"):
    client.get("/login")
    token = csrf_of(client)
    client.post("/register", data={
        "username": username, "password": password, "csrf_token": token,
    })
    response = client.post("/login", data={
        "username": username, "password": password, "csrf_token": token,
    })
    assert response.status_code == 302
    return csrf_of(client)


def call(client, token, method, url, payload=None):
    return client.open(
        url, method=method, json=payload, headers={"X-CSRF-Token": token}
    )


def test_login_is_required(app):
    client = app.test_client()
    assert client.get("/").status_code == 302
    assert client.get("/api/sessions").status_code == 401


def test_wrong_password_is_rejected(app):
    client = app.test_client()
    register_and_login(client)
    other = app.test_client()
    other.get("/login")
    response = other.post("/login", data={
        "username": "ana", "password": "errada",
        "csrf_token": csrf_of(other),
    })
    assert response.status_code == 401


def test_post_without_csrf_token_is_rejected(app):
    client = app.test_client()
    register_and_login(client)
    response = client.post("/api/sessions", json={"folder_name": "Fotos"})
    assert response.status_code == 400


def test_progress_survives_logout_and_new_login(app):
    first = app.test_client()
    token = register_and_login(first)
    opened = call(first, token, "POST", "/api/sessions",
                  {"folder_name": "Fotos"}).get_json()
    sid = opened["session"]["id"]
    base = f"/api/sessions/{sid}"
    call(first, token, "POST", f"{base}/destinations", {"name": "Viagem"})
    call(first, token, "PUT", f"{base}/decisions",
         {"path": "a.jpg", "action": "move", "destination": "viagem"})
    call(first, token, "PUT", f"{base}/decisions",
         {"path": "b.jpg", "action": "delete"})
    call(first, token, "DELETE", f"{base}/decisions", {"path": "b.jpg"})
    call(first, token, "PUT", f"{base}/decisions",
         {"path": "c.jpg", "action": "keep"})

    # "Outro dia": cookie novo, login de novo, mesma pasta.
    second = app.test_client()
    token2 = register_and_login(second)  # registro repetido é ignorado
    again = call(second, token2, "POST", "/api/sessions",
                 {"folder_name": "Fotos"}).get_json()

    assert again["session"]["id"] == sid
    assert again["session"]["destinations"] == ["Viagem"]
    restored = {d["path"]: d for d in again["decisions"]}
    assert set(restored) == {"a.jpg", "c.jpg"}
    assert restored["a.jpg"]["destination"] == "Viagem"

    summary = call(second, token2, "GET", f"{base}/summary").get_json()
    assert summary["by_action"] == {"move": 1, "delete": 0, "keep": 1}


def test_users_cannot_access_each_others_sessions(app):
    ana = app.test_client()
    ana_token = register_and_login(ana, "ana")
    sid = call(ana, ana_token, "POST", "/api/sessions",
               {"folder_name": "Fotos"}).get_json()["session"]["id"]

    bia = app.test_client()
    bia_token = register_and_login(bia, "bia")

    response = call(bia, bia_token, "PUT", f"/api/sessions/{sid}/decisions",
                    {"path": "a.jpg", "action": "delete"})
    assert response.status_code == 404
    assert call(bia, bia_token, "GET", "/api/sessions").get_json() == {
        "sessions": []
    }


def test_domain_errors_become_json_with_proper_status(app):
    client = app.test_client()
    token = register_and_login(client)
    sid = call(client, token, "POST", "/api/sessions",
               {"folder_name": "Fotos"}).get_json()["session"]["id"]
    base = f"/api/sessions/{sid}"

    bad_destination = call(client, token, "PUT", f"{base}/decisions",
                           {"path": "a.jpg", "action": "move",
                            "destination": "nao-existe"})
    bad_body = call(client, token, "PUT", f"{base}/decisions",
                    {"path": 123, "action": "keep"})

    assert bad_destination.status_code == 400
    assert "error" in bad_destination.get_json()
    assert bad_body.status_code == 400


def test_register_rejects_duplicate_username(app):
    client = app.test_client()
    client.get("/register")
    token = csrf_of(client)
    data = {"username": "ana", "password": "senha-segura",
            "csrf_token": token}
    assert client.post("/register", data=data).status_code == 302
    assert client.post("/register", data=data).status_code == 409
