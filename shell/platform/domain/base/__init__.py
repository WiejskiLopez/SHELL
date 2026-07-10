"""Platform base classes: Entity, AggregateRoot, EntityId and ValueObject."""

from __future__ import annotations

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.base.entity import Entity, TId
from shell.platform.domain.base.entity_id import EntityId
from shell.platform.domain.base.value_object import ValueObject

__all__ = [
    "AggregateRoot",
    "Entity",
    "EntityId",
    "TId",
    "ValueObject",
]
