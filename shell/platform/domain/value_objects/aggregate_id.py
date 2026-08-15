"""AggregateId value object for aggregate identification on events."""

from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.entity_id import EntityId


@dataclass(frozen=True, slots=True)
class AggregateId(EntityId):
    value: str
