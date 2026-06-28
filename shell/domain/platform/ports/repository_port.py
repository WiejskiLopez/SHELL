"""Generic repository port — shared protocol for all aggregate repositories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Protocol, TypeVar

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.exists_result import ExistsResult

TAggregate = TypeVar("TAggregate")
TId_co = TypeVar("TId_co", covariant=True)


class RepositoryPort(Protocol[TAggregate, TId_co]):
    """Minimal generic repository protocol.

    Every aggregate repository should extend this protocol so that
    the four canonical operations (get_by_id, save, delete, exists)
    are guaranteed to exist.
    """

    async def get_by_id(self, id: TId_co) -> TAggregate | None: ...

    async def save(self, entity: TAggregate) -> None: ...

    async def delete(self, id: TId_co) -> None: ...

    async def exists(self, id: TId_co) -> ExistsResult: ...
