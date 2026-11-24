import pytest

from domain.errors import ValidationError
from domain.sorting_session import (
    MAX_DESTINATIONS,
    SortingSession,
    normalize_folder_name,
)


def make_session():
    return SortingSession(user_id=1, folder_name="Fotos")


def test_add_destination_returns_normalized_name():
    session = make_session()
    assert session.add_destination("  Viagem ") == "Viagem"
    assert session.destinations == ["Viagem"]


def test_add_destination_rejects_duplicates_ignoring_case():
    session = make_session()
    session.add_destination("Viagem")
    with pytest.raises(ValidationError):
        session.add_destination("viagem")


@pytest.mark.parametrize(
    "name", ["", " ", ".", "..", "a/b", "a\\b", "nome:", "fim.", "x" * 61]
)
def test_add_destination_rejects_invalid_names(name):
    with pytest.raises(ValidationError):
        make_session().add_destination(name)


def test_add_destination_respects_limit():
    session = make_session()
    for number in range(MAX_DESTINATIONS):
        session.add_destination(f"pasta {number}")
    with pytest.raises(ValidationError):
        session.add_destination("uma a mais")


def test_find_destination_returns_canonical_name():
    session = make_session()
    session.add_destination("Viagem")
    assert session.find_destination(" VIAGEM ") == "Viagem"
    assert session.find_destination("Outra") is None


@pytest.mark.parametrize("raw", [None, "", "   ", "x" * 256])
def test_normalize_folder_name_rejects_invalid(raw):
    with pytest.raises(ValidationError):
        normalize_folder_name(raw)
