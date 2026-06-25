from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class GraphDefinitionId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphDefinitionId cannot be empty")

    def __str__(self) -> str:
        return self.value
