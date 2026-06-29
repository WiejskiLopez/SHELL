"""Generic in-memory repository — shared base for all InMemory* repositories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.exists_result import ExistsResult

TAggregate = TypeVar("TAggregate")
TId = TypeVar("TId")


class InMemoryRepository(Generic[TAggregate, TId]):
    """Base in-memory repository.

    Provides common get_by_id / save / delete / exists backed by a
    simple ``dict[str, TAggregate]``.  Concrete subclasses only need
    to provide BC-specific query methods.
    """

    def __init__(self) -> None:
        self._store: dict[str, TAggregate] = {}

    async def get_by_id(self, id: TId) -> TAggregate | None:
        key = id.value if hasattr(id, "value") else str(id)
        return self._store.get(key)

    async def save(self, entity: TAggregate) -> None:
        key = entity.id.value if hasattr(entity.id, "value") else str(entity.id)  # type: ignore[attr-defined]
        self._store[key] = entity

    async def delete(self, id: TId) -> None:
        key = id.value if hasattr(id, "value") else str(id)
        self._store.pop(key, None)

    async def exists(self, id: TId) -> ExistsResult:
        from shell.domain.platform.value_objects.exists_result import ExistsResult

        key = id.value if hasattr(id, "value") else str(id)
        return ExistsResult(key in self._store)
