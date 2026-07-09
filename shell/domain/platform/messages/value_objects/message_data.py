from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class MessageData(ValueObject):
    value: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.value)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MessageData:
        return cls(value=dict(data))
