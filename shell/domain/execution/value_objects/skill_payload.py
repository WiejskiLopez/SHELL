from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class SkillPayload(ValueObject):
    value: dict[str, str]

    def __post_init__(self) -> None:
        if not isinstance(self.value, dict):
            raise ValueError("SkillPayload.value must be a dict")
        for key, val in self.value.items():
            if not isinstance(key, str) or not isinstance(val, str):
                raise ValueError("SkillPayload keys and values must be strings")

    def __str__(self) -> str:
        return f"SkillPayload({len(self.value)} skills)"
