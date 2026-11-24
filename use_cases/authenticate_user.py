"""História 2: entrar na conta."""
from domain.errors import InvalidCredentialsError
from domain.user import User
from use_cases.ports import PasswordHasher, UserRepository


class AuthenticateUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher):
        self._users = users
        self._hasher = hasher

    def execute(self, username: str, password: str) -> User:
        user = self._users.find_by_username((username or "").strip().lower())
        if user is None or not self._hasher.verify(
            password or "", user.password_hash
        ):
            # Mensagem única: não revela se o usuário existe.
            raise InvalidCredentialsError("Usuário ou senha inválidos.")
        return user
