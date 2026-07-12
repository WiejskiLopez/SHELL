"""JsonStr — validated JSON string type (platform-level, not a domain ValueObject)."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JsonStr:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("JsonStr.value cannot be empty")
        try:
            json.loads(self.value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JsonStr.value is not valid JSON: {exc}") from exc

    def parse(self) -> dict[str, object]:
        return json.loads(self.value)

    def __str__(self) -> str:
        return self.value
