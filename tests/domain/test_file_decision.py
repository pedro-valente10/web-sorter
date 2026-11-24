import pytest

from domain.errors import ValidationError
from domain.file_decision import Action, FileDecision


def test_move_requires_destination():
    with pytest.raises(ValidationError):
        FileDecision(1, "a.jpg", Action.MOVE)


@pytest.mark.parametrize("action", [Action.DELETE, Action.KEEP])
def test_other_actions_reject_destination(action):
    with pytest.raises(ValidationError):
        FileDecision(1, "a.jpg", action, destination="Viagem")


@pytest.mark.parametrize("path", ["", "   ", "../segredo.txt", "a/../b"])
def test_rejects_invalid_paths(path):
    with pytest.raises(ValidationError):
        FileDecision(1, path, Action.KEEP)


def test_normalizes_path_separators():
    decision = FileDecision(1, "\\fotos\\a.jpg", Action.KEEP)
    assert decision.path == "fotos/a.jpg"


def test_mark_applied_returns_new_instance():
    original = FileDecision(1, "a.jpg", Action.DELETE)
    applied = original.mark_applied()
    assert applied.applied is True
    assert original.applied is False


def test_parse_action_rejects_unknown_value():
    with pytest.raises(ValidationError):
        Action.parse("explodir")
