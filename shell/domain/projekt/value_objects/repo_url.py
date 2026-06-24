from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RepoUrl(ValueObject):
    value: str | None

    def __post_init__(self) -> None:
        if self.value is not None and not self.value.strip():
            raise ValueError("RepoUrl cannot be empty string — use None instead")

    def __str__(self) -> str:
        return self.value or ""
