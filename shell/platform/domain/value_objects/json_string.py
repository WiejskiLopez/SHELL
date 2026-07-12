"""JsonString value object — validated JSON string."""

from __future__ import annotations

import json
from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class JsonString(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("JsonString.value cannot be empty")
        self._validate()

    def _validate(self) -> None:
        try:
            json.loads(self.value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JsonString.value is not valid JSON: {exc}") from exc

    def parse(self) -> dict[str, object]:
        return json.loads(self.value)

    def __str__(self) -> str:
        return self.value
