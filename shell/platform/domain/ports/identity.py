from __future__ import annotations

from typing import Protocol, TypeVar

from shell.platform.domain.base.entity_id import EntityId

TId = TypeVar("TId", bound=EntityId)


class IdGenerator(Protocol):
    def new_id(self, id_type: type[TId]) -> TId: ...
