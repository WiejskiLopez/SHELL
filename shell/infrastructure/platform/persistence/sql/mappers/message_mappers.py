"""Message domain entity <-> SQLAlchemy model mappers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.message import Message
    from shell.infrastructure.platform.persistence.sql.models.message.message import MessageModel


def message_entity_to_model(message: Message) -> MessageModel:

    mat = message.materialized_metadata
    return MessageModel(
        id=message.id.value,
        message_type=message.message_type.value,
        business_payload=message.business_payload.to_dict(),
        message_metadata=message.metadata.to_dict(),
        source=message.source.value,
        destination=message.destination.value,
        status=message.status.value,
        workflow_id=mat.workflow_id or None,
        step=mat.step or None,
        sequence_id=mat.sequence_id or None,
        source_node_execution_id=mat.source_node_execution_id or None,
        target_node_execution_id=mat.target_node_execution_id or None,
        source_role=mat.source_role or None,
        target_role=mat.target_role or None,
        created_at=message.created_at.value,
        received_at=message.received_at.value if message.received_at else None,
    )


def message_model_to_entity(model: MessageModel) -> Message:
    from shell.domain.platform.aggregates.message.message import Message
    from shell.domain.platform.aggregates.message.value_objects.business_payload import (
        BusinessPayload,
    )
    from shell.domain.platform.aggregates.message.value_objects.destination import Destination
    from shell.domain.platform.aggregates.message.value_objects.materialized_metadata import (
        MaterializedMetadata,
    )
    from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId
    from shell.domain.platform.aggregates.message.value_objects.message_metadata import (
        MessageMetadata,
    )
    from shell.domain.platform.aggregates.message.value_objects.message_status import MessageStatus
    from shell.domain.platform.aggregates.message.value_objects.message_type import MessageType
    from shell.domain.platform.aggregates.message.value_objects.source import Source
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.platform.value_objects.timestamp import Timestamp

    def _utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt

    received_at_dt = model.received_at
    received = Timestamp.from_datetime(received_at_dt.replace(tzinfo=UTC) if received_at_dt and received_at_dt.tzinfo is None else received_at_dt) if model.received_at else None  # type: ignore[arg-type]

    return Message.restore(
        id=MessageId(model.id),
        message_type=MessageType(model.message_type),
        business_payload=BusinessPayload(dict(model.business_payload or {})),
        metadata=MessageMetadata(dict(model.message_metadata or {})),
        source=Source(model.source),
        destination=Destination(model.destination),
        status=MessageStatus(model.status),
        materialized_metadata=MaterializedMetadata(
            workflow_id=model.workflow_id or "",
            step=model.step or 0,
            sequence_id=model.sequence_id or 0,
            source_node_execution_id=model.source_node_execution_id or "",
            target_node_execution_id=model.target_node_execution_id or "",
            source_role=model.source_role or "",
            target_role=model.target_role or "",
        ),
        created_at=CreatedAt.from_datetime(_utc(model.created_at)),  # type: ignore[arg-type]
        received_at=received,
    )
