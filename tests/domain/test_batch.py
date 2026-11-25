from datetime import datetime, timezone

import pytest

from domain.batch import (
    Batch,
    BatchItem,
    BatchKind,
    BatchProgress,
    BatchStatus,
    FileRef,
    ItemStatus,
)
from domain.errors import ValidationError

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_batch(kind=BatchKind.MOVE, **changes):
    values = {"sources": ("Fotos",), "destination": "Praia"}
    if kind is BatchKind.DELETE:
        values["destination"] = None
    values.update(changes)
    return Batch(user_id=1, kind=kind, **values)


def make_item(**changes):
    return BatchItem(position=0, source=0, name="a.jpg", **changes)


def test_rejects_unknown_kind():
    with pytest.raises(ValidationError):
        BatchKind.parse("rename")


def test_copy_and_move_need_a_destination():
    with pytest.raises(ValidationError):
        make_batch(BatchKind.COPY, destination=None)


def test_delete_does_not_accept_a_destination():
    with pytest.raises(ValidationError):
        make_batch(BatchKind.DELETE, destination="Praia")


@pytest.mark.parametrize("sources", [(), ("",), ("a/../b",), ("a//b",)])
def test_rejects_invalid_sources(sources):
    with pytest.raises(ValidationError):
        make_batch(sources=sources)


def test_plan_gives_free_names_across_sources():
    batch = make_batch(sources=("A", "B"))
    items = batch.plan(
        [FileRef(0, "x.jpg"), FileRef(1, "x.jpg"), FileRef(0, "y.jpg")],
        taken_names=["Y.JPG"],
    )
    assert [i.target_name for i in items] == [
        "x.jpg", "x (1).jpg", "y (1).jpg",
    ]
    assert [i.position for i in items] == [0, 1, 2]


def test_plan_for_delete_has_no_target_name():
    items = make_batch(BatchKind.DELETE).plan([FileRef(0, "x.jpg")], [])
    assert items[0].target_name is None


@pytest.mark.parametrize("files", [
    [],
    [FileRef(0, "x.jpg"), FileRef(0, "x.jpg")],
    [FileRef(1, "x.jpg")],
    [FileRef(-1, "x.jpg")],
    [FileRef(0, "../x.jpg")],
])
def test_plan_rejects_invalid_files(files):
    with pytest.raises(ValidationError):
        make_batch().plan(files, [])


def test_plan_limits_the_number_of_files(monkeypatch):
    monkeypatch.setattr("domain.batch.MAX_ITEMS", 1)
    with pytest.raises(ValidationError):
        make_batch().plan([FileRef(0, "a"), FileRef(0, "b")], [])


def test_settle_without_code_means_success():
    settled = make_batch().settle(make_item(), None, None)
    assert settled.status is ItemStatus.DONE


def test_settle_explains_the_failure_in_plain_language():
    settled = make_batch().settle(make_item(), "write", "NotAllowedError")
    assert settled.status is ItemStatus.FAILED
    assert settled.error == "Sem permissão para gravar na pasta de destino."


@pytest.mark.parametrize("step, code, expected", [
    ("write", "NoModificationAllowedError",
     "Sem permissão para gravar na pasta de destino."),
    ("read", "NotReadableError",
     "O arquivo está em uso ou mudou durante a leitura."),
    ("remove", "InvalidStateError",
     "O arquivo foi copiado, mas continua na origem. "
     "O arquivo está em uso por outro programa."),
])
def test_settle_explains_codes_seen_on_windows(step, code, expected):
    assert make_batch().settle(make_item(), step, code).error == expected


def test_settle_unknown_failure_has_a_default_message():
    settled = make_batch().settle(make_item(), "read", "Estranho")
    assert settled.error == "Não foi possível processar o arquivo."


def test_move_that_cannot_remove_the_original_is_a_failure():
    settled = make_batch().settle(
        make_item(), "remove", "NoModificationAllowedError"
    )
    assert settled.status is ItemStatus.FAILED
    assert settled.error.startswith("O arquivo foi copiado")


def test_deleting_a_file_that_is_already_gone_is_a_success():
    batch = make_batch(BatchKind.DELETE)
    settled = batch.settle(make_item(), "remove", "NotFoundError")
    assert settled.status is ItemStatus.DONE


def test_copying_a_file_that_is_gone_is_a_failure():
    batch = make_batch(BatchKind.COPY)
    settled = batch.settle(make_item(), "read", "NotFoundError")
    assert settled.error == "O arquivo não está mais na pasta de origem."


def test_settle_rejects_invalid_step():
    with pytest.raises(ValidationError):
        make_batch().settle(make_item(), "dance", "NotFoundError")


@pytest.mark.parametrize("status", [ItemStatus.DONE, ItemStatus.FAILED])
def test_an_item_has_a_single_result(status):
    with pytest.raises(ValidationError):
        make_batch().settle(make_item(status=status), None, None)


def test_finish_needs_every_file_settled():
    batch = make_batch()
    with pytest.raises(ValidationError):
        batch.finish(BatchProgress(total=3, done=1, failed=1), NOW)
    assert batch.is_open


def test_finish_closes_the_batch():
    batch = make_batch()
    batch.finish(BatchProgress(total=2, done=1, failed=1), NOW)
    assert batch.status is BatchStatus.FINISHED
    assert batch.finished_at == NOW


def test_closed_batch_accepts_nothing_else():
    batch = make_batch()
    batch.interrupt(NOW)
    assert batch.status is BatchStatus.INTERRUPTED
    with pytest.raises(ValidationError):
        batch.settle(make_item(), None, None)
    with pytest.raises(ValidationError):
        batch.finish(BatchProgress(), NOW)
    with pytest.raises(ValidationError):
        batch.interrupt(NOW)
