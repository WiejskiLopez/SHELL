from __future__ import annotations

from typing import Protocol, TypeVar

TId = TypeVar("TId")


class IdGenerator(Protocol):
    def new_id(self, id_type: type[TId]) -> TId: ...
