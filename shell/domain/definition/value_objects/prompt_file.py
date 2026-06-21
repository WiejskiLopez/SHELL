"""PromptFile value object."""

from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class PromptFile(ValueObject):
    file_name: str
    file_body: str

    def __post_init__(self) -> None:
        if not self.file_name:
            raise ValueError("PromptFile.file_name cannot be empty")

    def __str__(self) -> str:
        return f"PromptFile(file_name={self.file_name})"
