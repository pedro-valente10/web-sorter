"""API de lotes ponta a ponta: HTTP -> casos de uso -> SQLite real."""
import pytest

from app.config import Config
from app.main import create_app
from tests.app.test_routes import call, register_and_login


@pytest.fixture
def app(tmp_path):
    return create_app(
        Config(database_path=str(tmp_path / "t.db"), secret_key="teste")
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def api(client):
    token = register_and_login(client)
    return lambda method, url, payload=None: call(
        client, token, method, f"/api{url}", payload
    )


def move_request(**changes):
    payload = {
        "kind": "move",
        "sources": ["Fotos/Viagem"],
        "destination": "Fotos/Praia",
        "taken_names": ["a.jpg"],
        "files": [
            {"source": 0, "name": "a.jpg"},
            {"source": 0, "name": "b.jpg"},
        ],
    }
    payload.update(changes)
    return payload


def test_batches_require_login(app):
    assert app.test_client().get("/api/batches").status_code == 401


def test_extensions_summary(api):
    response = api("POST", "/extensions", {"files": ["a.pdf", "b.PDF"]})
    assert response.get_json() == {"extensions": [{
        "extension": ".pdf",
        "description": "Arquivos PDF",
        "count": 2,
        "indexes": [0, 1],
    }]}


def test_target_name(api):
    response = api("POST", "/target-name", {
        "name": "a.jpg", "taken_names": ["a.jpg"],
    })
    assert response.get_json() == {"name": "a (1).jpg"}


def test_plan_does_not_create_history(api):
    plan = api("POST", "/batches/plan", move_request()).get_json()
    assert plan["id"] is None
    assert plan["items"][0]["target_name"] == "a (1).jpg"
    assert api("GET", "/batches").get_json() == {"batches": []}


def test_full_batch_with_one_failure(api):
    started = api("POST", "/batches", move_request())
    assert started.status_code == 201
    url = f"/batches/{started.get_json()['id']}"

    api("POST", f"{url}/items/0/result", {})
    failed = api("POST", f"{url}/items/1/result", {
        "step": "write", "code": "NotAllowedError",
    }).get_json()
    finished = api("POST", f"{url}/finish", {}).get_json()

    assert failed["error"] == (
        "Sem permissão para gravar na pasta de destino."
    )
    assert finished["status"] == "finished"
    assert finished["progress"] == {
        "total": 2, "done": 1, "failed": 1, "pending": 0,
    }
    [listed] = api("GET", "/batches").get_json()["batches"]
    assert listed["progress"]["failed"] == 1
    assert "items" not in listed


def test_interrupted_batch_is_resumed_by_a_new_login(app, api):
    batch_id = api("POST", "/batches", move_request()).get_json()["id"]
    api("POST", f"/batches/{batch_id}/items/0/result", {})

    other = app.test_client()
    token = register_and_login(other)
    resumed = call(
        other, token, "POST", f"/api/batches/{batch_id}/resume",
        {"taken_names": ["b.jpg"]},
    ).get_json()

    assert [i["name"] for i in resumed["items"]] == ["b.jpg"]
    assert resumed["items"][0]["target_name"] == "b (1).jpg"


def test_discard_closes_the_batch(api):
    batch_id = api("POST", "/batches", move_request()).get_json()["id"]
    discarded = api("POST", f"/batches/{batch_id}/discard", {})
    assert discarded.get_json()["status"] == "interrupted"
    again = api("POST", f"/batches/{batch_id}/resume", {"taken_names": []})
    assert again.status_code == 400


def test_users_cannot_see_each_others_batches(app, api):
    batch_id = api("POST", "/batches", move_request()).get_json()["id"]
    bia = app.test_client()
    token = register_and_login(bia, "bia")
    response = call(bia, token, "GET", f"/api/batches/{batch_id}")
    assert response.status_code == 404


@pytest.mark.parametrize("changes", [
    {"kind": 1},
    {"sources": "Fotos"},
    {"files": "a.jpg"},
    {"files": ["a.jpg"]},
    {"files": [{"source": True, "name": "a.jpg"}]},
    {"files": [{"source": 0, "name": None}]},
    {"taken_names": [1]},
    {"same_folder": "sim"},
    {"same_folder": True},
])
def test_invalid_payloads_are_rejected(api, changes):
    response = api("POST", "/batches", move_request(**changes))
    assert response.status_code == 400
    assert "error" in response.get_json()
