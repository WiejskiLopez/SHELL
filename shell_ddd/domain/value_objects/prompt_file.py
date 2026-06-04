"""PromptFile value object."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptFile:
    file_name: str
    file_body: str

    def __post_init__(self) -> None:
        if not self.file_name:
            raise ValueError("PromptFile.file_name cannot be empty")
