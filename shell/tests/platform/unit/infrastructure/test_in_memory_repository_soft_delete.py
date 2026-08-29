"""Kontrakt InMemoryRepository — exists/delete z VO `_deleted_at`.

Platformowy base musi jednolicie odróżniać rekord istniejący (brak soft-delete)
od nieistniejącego/usuniętego, niezależnie od tego, czy agregat inicjalizuje
`_deleted_at` jako Value Object, czy pozostawia atrybut nieustawiony.
"""

from __future__ import annotations

from datetime import UTC, datetime

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.base.entity_id import EntityId
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository


def _now() -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC)


class _SampleId(EntityId):
    pass


class _SampleAggregate(AggregateRoot[_SampleId]):
    __slots__ = ("_deleted_at",)

    def __init__(self, id: _SampleId) -> None:
        super().__init__(id)
        object.__setattr__(self, "_deleted_at", DeletedAt.none())


class _UninitializedAggregate(AggregateRoot[_SampleId]):
    __slots__ = ()


class TestInMemoryRepositoryDoesExists:
    async def test_exists_true_for_vo_deleted_at_none(self) -> None:
        repository = InMemoryRepository[_SampleAggregate, _SampleId]()
        aggregate = _SampleAggregate(_SampleId("a1"))
        await repository.save(aggregate)

        result = await repository.exists(_SampleId("a1"))
        assert isinstance(result, ExistsResult)
        assert result.value is True

    async def test_exists_false_after_soft_delete_vo(self) -> None:
        repository = InMemoryRepository[_SampleAggregate, _SampleId]()
        aggregate = _SampleAggregate(_SampleId("a1"))
        await repository.save(aggregate)
        await repository.delete(_SampleId("a1"))

        result = await repository.exists(_SampleId("a1"))
        assert result.value is False

    async def test_exists_true_for_uninitialized_slot_and_false_for_missing(self) -> None:
        repository = InMemoryRepository[_UninitializedAggregate, _SampleId]()
        aggregate = _UninitializedAggregate(_SampleId("b1"))
        await repository.save(aggregate)

        assert (await repository.exists(_SampleId("b1"))).value is True
        assert (await repository.exists(_SampleId("missing"))).value is False

    async def test_exists_false_when_deleted_at_has_value(self) -> None:
        repository = InMemoryRepository[_SampleAggregate, _SampleId]()
        aggregate = _SampleAggregate(_SampleId("c1"))
        await repository.save(aggregate)
        object.__setattr__(aggregate, "_deleted_at", DeletedAt.from_datetime(_now()))

        assert (await repository.exists(_SampleId("c1"))).value is False
