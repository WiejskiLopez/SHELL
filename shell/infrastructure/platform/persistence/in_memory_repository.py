"""Generic in-memory repository — shared base for all InMemory* repositories."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Generic, TypeVar

from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.exists_result import ExistsResult

TAggregate = TypeVar("TAggregate")
TId = TypeVar("TId")


class InMemoryRepository(Generic[TAggregate, TId]):
    """Base in-memory repository.

    Provides common get_by_id / save / delete / exists backed by a
    simple ``dict[str, TAggregate]``.  Concrete subclasses only need
    to provide BC-specific query methods.

    ``delete`` performs a soft-delete by setting ``_deleted_at`` on the
    entity via ``object.__setattr__`` (bypasses frozen dataclass immutability).
    ``exists`` returns ``False`` for soft-deleted entities.
    """

    def __init__(self) -> None:
        self._store: dict[str, TAggregate] = {}

    async def get_by_id(self, id: TId) -> TAggregate | None:
        key = id.value if hasattr(id, "value") else str(id)
        return self._store.get(key)

    async def save(self, entity: TAggregate) -> None:
        key = entity.id.value if hasattr(entity.id, "value") else str(entity.id)  # type: ignore[attr-defined]
        self._store[key] = entity

    async def delete(self, id: TId, now: datetime | None = None) -> None:
        key = id.value if hasattr(id, "value") else str(id)
        entity = self._store.get(key)
        if entity is not None:
            dt = now if now is not None and now.tzinfo is not None else (now or datetime.now(tz=UTC)).replace(tzinfo=UTC)
            object.__setattr__(entity, "_deleted_at", DeletedAt.from_datetime(dt))

    async def exists(self, id: TId) -> ExistsResult:
        key = id.value if hasattr(id, "value") else str(id)
        entity = self._store.get(key)
        if entity is None:
            return ExistsResult(False)
        deleted = getattr(entity, "_deleted_at", None)
        return ExistsResult(deleted is None)
