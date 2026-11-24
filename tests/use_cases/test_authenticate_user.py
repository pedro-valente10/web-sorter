import pytest

from domain.errors import InvalidCredentialsError
from use_cases.authenticate_user import AuthenticateUser
from use_cases.register_user import RegisterUser


@pytest.fixture
def authenticate(users, hasher):
    RegisterUser(users, hasher).execute("ana", "senha-segura")
    return AuthenticateUser(users, hasher)


def test_returns_user_with_correct_credentials(authenticate):
    assert authenticate.execute(" Ana ", "senha-segura").username == "ana"


def test_rejects_wrong_password(authenticate):
    with pytest.raises(InvalidCredentialsError):
        authenticate.execute("ana", "errada")


def test_unknown_user_gets_same_error_as_wrong_password(authenticate):
    with pytest.raises(InvalidCredentialsError) as unknown:
        authenticate.execute("ninguem", "senha-segura")
    with pytest.raises(InvalidCredentialsError) as wrong:
        authenticate.execute("ana", "errada")
    assert str(unknown.value) == str(wrong.value)


@pytest.mark.parametrize("username, password", [(None, None), ("", "")])
def test_handles_empty_input(authenticate, username, password):
    with pytest.raises(InvalidCredentialsError):
        authenticate.execute(username, password)
