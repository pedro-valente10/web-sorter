import pytest

from domain.errors import ValidationError
from domain.user import normalize_username, validate_password


def test_normalize_username_strips_and_lowercases():
    assert normalize_username("  Maria_Silva ") == "maria_silva"


@pytest.mark.parametrize("raw", [None, "", "ab", "a b c", "x" * 31, "açaí"])
def test_normalize_username_rejects_invalid(raw):
    with pytest.raises(ValidationError):
        normalize_username(raw)


def test_validate_password_accepts_minimum_length():
    validate_password("12345678")


@pytest.mark.parametrize("raw", [None, "", "1234567"])
def test_validate_password_rejects_short(raw):
    with pytest.raises(ValidationError):
        validate_password(raw)
