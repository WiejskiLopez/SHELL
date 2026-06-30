"""Generic repository port — shared protocol for all aggregate repositories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.exists_result import ExistsResult

TAggregate = TypeVar("TAggregate")
TId = TypeVar("TId")


class RepositoryPort(Protocol[TAggregate, TId]):  # type: ignore[misc]
    """Minimal generic repository protocol.

    Every aggregate repository should extend this protocol so that
    the four canonical operations (get_by_id, save, delete, exists)
    are guaranteed to exist.
    """

    async def get_by_id(self, id: TId) -> TAggregate | None: ...

    async def save(self, entity: TAggregate) -> None: ...

    async def delete(self, id: TId) -> None: ...

    async def exists(self, id: TId) -> ExistsResult: ...
