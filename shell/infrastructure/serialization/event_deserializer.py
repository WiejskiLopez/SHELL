from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.events.events import (
    DomainEvent,
    EnvelopeDeadlettered,
    EnvelopeExpired,
    EnvelopeRouted,
    GraphExecutionBuilt,
    GraphNodeExecutionAdvanced,
    GraphNodeExecutionCompleted,
    GraphNodeExecutionFailed,
    GraphNodeExecutionRequested,
    GraphNodeExecutionStarted,
    TaskExecutionCreated,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from shell.infrastructure.serialization import DomainEventSerializer

logger = logging.getLogger(__name__)


class EventDeserializer:
    def __init__(self) -> None:
        self._registry: dict[str, type[DomainEvent]] = {
            "EnvelopeDeadlettered": EnvelopeDeadlettered,
            "TaskExecutionCreated": TaskExecutionCreated,
            "GraphExecutionBuilt": GraphExecutionBuilt,
            "WorkflowStarted": WorkflowStarted,
            "EnvelopeRouted": EnvelopeRouted,
            "EnvelopeExpired": EnvelopeExpired,
            "GraphNodeExecutionCompleted": GraphNodeExecutionCompleted,
            "GraphNodeExecutionFailed": GraphNodeExecutionFailed,
            "WorkflowCompleted": WorkflowCompleted,
            "WorkflowFailed": WorkflowFailed,
            "GraphNodeExecutionRequested": GraphNodeExecutionRequested,
            "GraphNodeExecutionStarted": GraphNodeExecutionStarted,
            "GraphNodeExecutionAdvanced": GraphNodeExecutionAdvanced,
        }
        self._serializer = DomainEventSerializer()

    def deserialize(
        self,
        event_type: str,
        occurred_at: datetime,
        payload: dict[str, Any],
        schema_version: int = 1,
    ) -> DomainEvent | None:
        event_cls = self._registry.get(event_type)

        if not event_cls:
            logger.error("Unknown event type: %s", event_type)
            return None

        try:
            return self._serializer.from_payload(
                event_cls=event_cls,
                occurred_at=occurred_at,
                payload=payload,
                schema_version=schema_version,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error("Failed to deserialize event %s: %s", event_type, e)
            return None
