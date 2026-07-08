from __future__ import annotations

from dataclasses import dataclass, field

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class MessageMetadata(ValueObject):
    value: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.value is None:
            object.__setattr__(self, "value", {})

    def to_dict(self) -> dict[str, object]:
        return dict(self.value)
