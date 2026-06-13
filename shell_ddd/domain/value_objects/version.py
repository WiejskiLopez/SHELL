"""Version value object — monotonically increasing positive integer."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Version:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError(f"Version must be >= 1, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)

    def next(self) -> Version:
        return Version(self.value + 1)

    @classmethod
    def initial(cls) -> Version:
        return cls(1)
