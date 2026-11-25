import pytest

from domain.errors import ValidationError
from domain.file_name import (
    NameAllocator,
    describe_extension,
    extension_of,
    validate_file_name,
)


@pytest.mark.parametrize("name, expected", [
    ("foto.jpg", ".jpg"),
    ("FOTO.JPG", ".jpg"),
    ("a.tar.gz", ".gz"),
    ("LEIAME", ""),
    (".gitignore", ""),
    ("ponto.", ""),
])
def test_extension_ignores_case_and_hidden_files(name, expected):
    assert extension_of(name) == expected


def test_extension_descriptions():
    assert describe_extension(".pdf") == "Arquivos PDF"
    assert describe_extension(".xyz") == "Arquivos XYZ"
    assert describe_extension("") == "Arquivos sem extensão"


@pytest.mark.parametrize(
    "name", ["", "  ", ".", "..", "a/b.jpg", "a\\b.jpg", "x" * 256, None]
)
def test_rejects_anything_that_is_not_a_plain_file_name(name):
    with pytest.raises(ValidationError):
        validate_file_name(name)


def test_allocator_keeps_free_names():
    assert NameAllocator().allocate("foto.jpg") == "foto.jpg"


def test_allocator_adds_suffix_before_the_extension():
    names = NameAllocator(["foto.jpg", "foto (1).jpg"])
    assert names.allocate("foto.jpg") == "foto (2).jpg"


def test_allocator_ignores_case_like_windows():
    assert NameAllocator(["FOTO.JPG"]).allocate("foto.jpg") == "foto (1).jpg"


def test_allocator_never_repeats_a_name_it_gave():
    names = NameAllocator()
    given = [names.allocate("foto.jpg") for _ in range(3)]
    assert given == ["foto.jpg", "foto (1).jpg", "foto (2).jpg"]


def test_allocator_respects_a_literal_suffix_from_another_file():
    names = NameAllocator()
    given = [
        names.allocate(n) for n in ("a.jpg", "a (1).jpg", "a.jpg")
    ]
    assert given == ["a.jpg", "a (1).jpg", "a (2).jpg"]


def test_allocator_handles_names_without_extension():
    assert NameAllocator(["LEIAME"]).allocate("LEIAME") == "LEIAME (1)"
