from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.ingestion.domain.ingestion.aggregates.ingestion.ingestion import Ingestion
from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_context import (
    IngestionContext,
)
from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_data import (
    IngestionData,
)
from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
    IngestionId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.types import JsonStr


class TestIngestion:
    def test_new_creates_message(self) -> None:
        now = CreatedAt.from_datetime(datetime.now(tz=UTC))
        message = Ingestion.new(
            id_=IngestionId.generate(),
            ingestion_data=IngestionData(JsonStr(json.dumps({"key": "value", "type": "test"}))),
            ingestion_context=IngestionContext(JsonStr(json.dumps({"channel": "email"}))),
            now=now,
        )

        assert json.loads(message.ingestion_data.value.value) == {"key": "value", "type": "test"}
        assert json.loads(message.ingestion_context.value.value) == {"channel": "email"}
        assert message.created_at is not None
        assert message.created_at.value == now.value

    def test_new_generates_created_event(self) -> None:
        now = CreatedAt.from_datetime(datetime.now(tz=UTC))
        message = Ingestion.new(
            id_=IngestionId.generate(),
            ingestion_data=IngestionData(JsonStr(json.dumps({"type": "test"}))),
            ingestion_context=IngestionContext(JsonStr(json.dumps({"channel": "email"}))),
            now=now,
        )

        events = message.pull_events()
        assert len(events) == 1
        event = events[0]
        assert event.aggregate_id.value == message.id.value

    def test_restore_preserves_fields(self) -> None:
        now = datetime.now(tz=UTC)
        msg_id = IngestionId.generate()
        data = IngestionData(JsonStr(json.dumps({"foo": "bar"})))
        context = IngestionContext(JsonStr(json.dumps({"channel": "slack"})))

        restored = Ingestion.restore(
            id=msg_id,
            ingestion_data=data,
            ingestion_context=context,
            created_at=CreatedAt.from_datetime(now),
        )

        assert restored.id == msg_id
        assert restored.ingestion_data == data
        assert restored.ingestion_context == context
        assert restored.created_at is not None
        assert restored.created_at.value == now
