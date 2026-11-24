import pytest

from domain.errors import ValidationError
from domain.file_decision import Action, FileDecision


def test_creates_session_on_first_open(open_session):
    state = open_session.execute(1, " Fotos ")
    assert state.session.id is not None
    assert state.session.folder_name == "Fotos"
    assert state.session.user_id == 1
    assert state.decisions == []


def test_reopening_returns_same_session_with_saved_decisions(
    open_session, decisions
):
    first = open_session.execute(1, "Fotos")
    saved = FileDecision(first.session.id, "a.jpg", Action.DELETE)
    decisions.save(saved)

    again = open_session.execute(1, "Fotos")

    assert again.session.id == first.session.id
    assert again.decisions == [saved]


def test_reopening_refreshes_last_activity(open_session):
    first = open_session.execute(1, "Fotos").session.updated_at
    second = open_session.execute(1, "Fotos").session.updated_at
    assert second > first


def test_users_do_not_share_sessions_for_same_folder(open_session):
    mine = open_session.execute(1, "Fotos").session
    theirs = open_session.execute(2, "Fotos").session
    assert mine.id != theirs.id


def test_rejects_empty_folder_name(open_session):
    with pytest.raises(ValidationError):
        open_session.execute(1, "   ")
