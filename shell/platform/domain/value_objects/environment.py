from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Environment(ValueObject):
    os: str
    runtime: str
    cwd: str

    def __post_init__(self) -> None:
        if not self.os:
            raise ValueError("Environment.os cannot be empty")
        if not self.runtime:
            raise ValueError("Environment.runtime cannot be empty")
        if not self.cwd:
            raise ValueError("Environment.cwd cannot be empty")

    def __str__(self) -> str:
        return f"{self.os}/{self.runtime}"
