from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class SkillData(ValueObject):
    value: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", dict(self.value) if self.value else {})

    def get(self, key: str, default: Any = None) -> Any:
        return self.value.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.value)
