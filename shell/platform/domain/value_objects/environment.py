from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError


@dataclass(frozen=True, slots=True)
class Environment(ValueObject):
    os: str
    runtime: str
    cwd: str

    def __post_init__(self) -> None:
        if not self.os:
            raise DomainError("Environment.os cannot be empty")
        if not self.runtime:
            raise DomainError("Environment.runtime cannot be empty")
        if not self.cwd:
            raise DomainError("Environment.cwd cannot be empty")

    def __str__(self) -> str:
        return f"{self.os}/{self.runtime}"
