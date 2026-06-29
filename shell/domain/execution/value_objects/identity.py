from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Identity(ValueObject):
    value: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.value, dict):
            raise ValueError("Identity.value must be a dict")

    def __str__(self) -> str:
        return f"Identity({len(self.value)} keys)"
