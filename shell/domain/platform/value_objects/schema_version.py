"""SchemaVersion value object for event schema versioning."""

from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class SchemaVersion(ValueObject):
    value: int
