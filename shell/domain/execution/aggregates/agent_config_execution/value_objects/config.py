from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Config(ValueObject):
    model: str
    temperature: float
    max_tokens: int
    top_p: float

    def __post_init__(self) -> None:
        if not self.model:
            raise ValueError("Config.model cannot be empty")
        if self.temperature < 0:
            raise ValueError("Config.temperature cannot be negative")
        if self.max_tokens < 1:
            raise ValueError("Config.max_tokens must be >= 1")
        if self.top_p < 0 or self.top_p > 1:
            raise ValueError("Config.top_p must be between 0 and 1")

    def __str__(self) -> str:
        return f"Config(model={self.model})"
