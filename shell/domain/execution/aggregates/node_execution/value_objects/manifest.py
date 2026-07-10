"""Manifest value object — parsed manifest.yaml metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.base.value_object import ValueObject

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.mode import Mode


@dataclass(frozen=True, slots=True)
class Manifest(ValueObject):
    name: str
    mode: Mode
    role: str
    node_type: str
    version: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Manifest.name cannot be empty")
        if not self.role:
            raise ValueError("Manifest.role cannot be empty")

    def __str__(self) -> str:
        return f"Manifest(name={self.name}, mode={self.mode})"
