from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Embedding(ValueObject):
    value: bytes

    def __str__(self) -> str:
        return f"<{len(self.value)} bytes>"
