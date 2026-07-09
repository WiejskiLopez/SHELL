from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class MaxSubgraphDepth(ValueObject):
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError(f"MaxSubgraphDepth must be >= 1, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def default(cls) -> MaxSubgraphDepth:
        return cls(5)
