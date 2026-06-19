"""Domain primitives: Entity and AggregateRoot base classes."""
from __future__ import annotations


from shell.domain.entities.base.aggregate_root import AggregateRoot
from shell.domain.entities.base.entity import Entity, TId

__all__ = [
    "AggregateRoot",
    "Entity",
    "TId",
]
