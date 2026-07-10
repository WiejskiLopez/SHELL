"""ConditionExpression value object — shared across definition and execution BCs."""

from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class ConditionExpression(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ConditionExpression cannot be empty")

    def __str__(self) -> str:
        return self.value
