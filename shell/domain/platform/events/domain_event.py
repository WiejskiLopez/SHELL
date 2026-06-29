from __future__ import annotations

from dataclasses import dataclass, field

from shell.domain.platform.value_objects.aggregate_id import AggregateId
from shell.domain.platform.value_objects.aggregate_type import AggregateType
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.event_id import EventId
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    event_id: EventId = field(default_factory=EventId.generate)
    aggregate_id: AggregateId = field(default_factory=lambda: AggregateId(""))
    aggregate_type: AggregateType = field(default_factory=lambda: AggregateType(""))
    occurred_at: CreatedAt
    schema_version: SchemaVersion = field(default_factory=lambda: SchemaVersion(1))
