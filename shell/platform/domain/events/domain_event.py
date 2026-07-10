from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.aggregate_id import AggregateId
from shell.platform.domain.value_objects.aggregate_type import AggregateType
from shell.platform.domain.value_objects.event_id import EventId
from shell.platform.domain.value_objects.schema_version import SchemaVersion

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    event_id: EventId = field(default_factory=EventId.generate)
    aggregate_id: AggregateId = field(default_factory=lambda: AggregateId(""))
    aggregate_type: AggregateType = field(default_factory=lambda: AggregateType(""))
    occurred_at: CreatedAt
    schema_version: SchemaVersion = field(default_factory=lambda: SchemaVersion(1))
