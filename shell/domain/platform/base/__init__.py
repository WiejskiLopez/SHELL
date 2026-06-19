"""Platform base classes: Entity and AggregateRoot."""

from __future__ import annotations

from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.base.entity import Entity, TId

__all__ = [
    "AggregateRoot",
    "Entity",
    "TId",
]
