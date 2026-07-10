from __future__ import annotations

from typing import TypeVar

from shell.platform.domain.base.entity_id import EntityId

TId = TypeVar("TId", bound=EntityId)


class FakeIdGenerator:
    def __init__(self) -> None:
        self._counter = 0

    def _next(self) -> str:
        self._counter += 1
        return f"00000000-0000-0000-0000-{self._counter:012d}"

    def new_id(self, id_type: type[TId]) -> TId:
        return id_type(self._next())
