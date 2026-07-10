from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class DataMapping(ValueObject):
    value: dict[str, Any]

    def __str__(self) -> str:
        return str(self.value)
