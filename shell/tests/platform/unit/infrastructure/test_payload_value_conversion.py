from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell.platform.domain.value_objects.aggregate_id import AggregateId
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.serialization.payload.payload_value_deserializer import (
    PayloadValueDeserializer,
)
from shell.platform.infrastructure.serialization.payload.payload_value_serializer import (
    PayloadValueSerializer,
)


@dataclass(frozen=True, slots=True)
class NestedPayload:
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class PayloadWithAllSupportedValues:
    text: str
    number: int
    ratio: float
    enabled: bool
    timestamp: datetime
    created_at: CreatedAt
    occurred_at: OccurredAt
    aggregate_ids: list[AggregateId]
    counts: dict[str, int]
    tags: tuple[str, ...]
    flags: set[int]
    optional_text: str | None
    nested: NestedPayload


def test_payload_value_round_trip_supports_scalars_collections_and_value_objects() -> None:
    timestamp = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    source = PayloadWithAllSupportedValues(
        text="payload",
        number=7,
        ratio=1.5,
        enabled=True,
        timestamp=timestamp,
        created_at=CreatedAt.from_datetime(timestamp),
        occurred_at=OccurredAt.from_datetime(timestamp),
        aggregate_ids=[AggregateId("aggregate-1")],
        counts={"ready": 2},
        tags=("one", "two"),
        flags={1, 2},
        optional_text=None,
        nested=NestedPayload(label="nested", count=3),
    )

    serialized = PayloadValueSerializer().serialize(source)
    restored = PayloadValueDeserializer().deserialize(
        serialized,
        PayloadWithAllSupportedValues,
    )

    assert restored == source
    assert isinstance(restored, PayloadWithAllSupportedValues)
    assert isinstance(restored.created_at, CreatedAt)
    assert isinstance(restored.occurred_at, OccurredAt)
    assert isinstance(restored.aggregate_ids[0], AggregateId)
    assert isinstance(restored.nested, NestedPayload)
