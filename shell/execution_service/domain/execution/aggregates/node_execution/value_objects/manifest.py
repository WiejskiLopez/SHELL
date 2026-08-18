"""Manifest value object — parsed manifest.yaml metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.mode import (
        Mode,
    )


@dataclass(frozen=True, slots=True)
class Manifest(ValueObject):
    name: str
    mode: Mode
    role: str
    node_type: str
    version: str

    def __post_init__(self) -> None:
        if not self.name:
            raise DomainError("Manifest.name cannot be empty")
        if not self.role:
            raise DomainError("Manifest.role cannot be empty")

    def __str__(self) -> str:
        return f"Manifest(name={self.name}, mode={self.mode})"
