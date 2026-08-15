from __future__ import annotations

from dataclasses import dataclass, field

from shell.platform.domain.value_objects.aggregate_id import AggregateId
from shell.platform.domain.value_objects.aggregate_name import AggregateName
from shell.platform.domain.value_objects.message_id import MessageId
from shell.platform.domain.value_objects.occurred_at import (  # noqa: TC001 -- needed at runtime for deserialization type resolution
    OccurredAt,
)
from shell.platform.domain.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainMessage:
    message_id: MessageId = field(default_factory=MessageId.generate)
    aggregate_id: AggregateId = field(default_factory=AggregateId.generate)
    aggregate_name: AggregateName = field(default_factory=lambda: AggregateName(""))
    occurred_at: OccurredAt
    schema_version: SchemaVersion = field(default_factory=lambda: SchemaVersion(1))
