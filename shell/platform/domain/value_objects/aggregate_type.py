"""AggregateType value object — stores the aggregate class name on events."""

from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class AggregateType(ValueObject):
    value: str
