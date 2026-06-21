"""Platform base classes: Entity, AggregateRoot and ValueObject."""

from __future__ import annotations

from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.base.entity import Entity, TId
from shell.domain.platform.base.value_object import ValueObject

__all__ = [
    "AggregateRoot",
    "Entity",
    "TId",
    "ValueObject",
]
