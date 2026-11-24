"""UserRepository sobre SQLite."""
import sqlite3
from dataclasses import replace

from domain.errors import UsernameAlreadyExistsError
from domain.user import User
from infra.db.database import Database
from use_cases.ports import UserRepository


class SqliteUserRepository(UserRepository):
    def __init__(self, database: Database):
        self._db = database

    def add(self, user: User) -> User:
        try:
            with self._db.connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash) "
                    "VALUES (?, ?)",
                    (user.username, user.password_hash),
                )
        except sqlite3.IntegrityError:
            raise UsernameAlreadyExistsError(
                "Esse usuário já existe."
            ) from None
        return replace(user, id=cursor.lastrowid)

    def find_by_username(self, username: str) -> User | None:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash FROM users "
                "WHERE username = ?",
                (username,),
            ).fetchone()
        if row is None:
            return None
        return User(row["id"], row["username"], row["password_hash"])
