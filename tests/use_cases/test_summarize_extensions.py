import pytest

from domain.errors import ValidationError
from use_cases.resolve_target_name import ResolveTargetName
from use_cases.summarize_extensions import SummarizeExtensions


def test_groups_from_most_to_least_common():
    groups = SummarizeExtensions().execute(
        ["a.pdf", "b.JPG", "c.jpg", "LEIAME"]
    )
    assert [(g.extension, g.count) for g in groups] == [
        (".jpg", 2), ("", 1), (".pdf", 1),
    ]


def test_groups_point_to_the_original_files():
    groups = SummarizeExtensions().execute(["a.pdf", "b.JPG", "c.jpg"])
    assert groups[0].indexes == [1, 2]
    assert groups[0].description == "Imagens JPEG"


def test_empty_folder_has_no_groups():
    assert SummarizeExtensions().execute([]) == []


def test_rejects_paths():
    with pytest.raises(ValidationError):
        SummarizeExtensions().execute(["sub/a.pdf"])


def test_limits_the_number_of_files(monkeypatch):
    monkeypatch.setattr("use_cases.summarize_extensions.MAX_ITEMS", 1)
    with pytest.raises(ValidationError):
        SummarizeExtensions().execute(["a.pdf", "b.pdf"])


def test_resolve_target_name_avoids_existing_files():
    resolve = ResolveTargetName()
    assert resolve.execute("a.jpg", []) == "a.jpg"
    assert resolve.execute("a.jpg", ["A.jpg"]) == "a (1).jpg"
    with pytest.raises(ValidationError):
        resolve.execute("../a.jpg", [])
