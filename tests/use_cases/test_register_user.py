import pytest

from domain.errors import UsernameAlreadyExistsError, ValidationError
from use_cases.register_user import RegisterUser


@pytest.fixture
def register(users, hasher):
    return RegisterUser(users, hasher)


def test_registers_user_with_hashed_password(register, users):
    user = register.execute("  Ana ", "senha-segura")
    assert user.id is not None
    assert user.username == "ana"
    assert user.password_hash == "hashed:senha-segura"
    assert users.find_by_username("ana") == user


def test_rejects_duplicate_username_ignoring_case(register):
    register.execute("ana", "senha-segura")
    with pytest.raises(UsernameAlreadyExistsError):
        register.execute("ANA", "outra-senha")


def test_rejects_weak_password_without_saving(register, users):
    with pytest.raises(ValidationError):
        register.execute("ana", "123")
    assert users.users == {}


def test_rejects_invalid_username(register):
    with pytest.raises(ValidationError):
        register.execute("a", "senha-segura")
