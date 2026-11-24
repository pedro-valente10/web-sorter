"""História 1: criar uma conta."""
from domain.errors import UsernameAlreadyExistsError
from domain.user import User, normalize_username, validate_password
from use_cases.ports import PasswordHasher, UserRepository


class RegisterUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher):
        self._users = users
        self._hasher = hasher

    def execute(self, username: str, password: str) -> User:
        normalized = normalize_username(username)
        validate_password(password)
        if self._users.find_by_username(normalized) is not None:
            raise UsernameAlreadyExistsError("Esse usuário já existe.")
        user = User(
            id=None,
            username=normalized,
            password_hash=self._hasher.hash(password),
        )
        return self._users.add(user)
