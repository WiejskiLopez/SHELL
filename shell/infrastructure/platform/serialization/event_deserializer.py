from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.events import (
    DomainEvent,
    EnvelopeDeadletteredEvent,
    EnvelopeExpiredEvent,
    EnvelopeRoutedEvent,
    GraphExecutionBuiltEvent,
    GraphNodeExecutionAdvancedEvent,
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionConditionEvaluatedEvent,
    GraphNodeExecutionFailedEvent,
    GraphNodeExecutionJoinReadyEvent,
    GraphNodeExecutionLoopIterationEvent,
    GraphNodeExecutionRequestedEvent,
    GraphNodeExecutionStartedEvent,
    GraphNodeExecutionTimedOutEvent,
    GraphNodeParallelExecutionRequestedEvent,
    TaskExecutionCreatedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
)
from shell.infrastructure.platform.serialization import DomainEventSerializer

logger = logging.getLogger(__name__)


class EventDeserializer:
    def __init__(self) -> None:
        self._registry: dict[str, type[DomainEvent]] = {
            "EnvelopeDeadlettered": EnvelopeDeadletteredEvent,
            "TaskExecutionCreated": TaskExecutionCreatedEvent,
            "GraphExecutionBuilt": GraphExecutionBuiltEvent,
            "WorkflowStarted": WorkflowStartedEvent,
            "EnvelopeRouted": EnvelopeRoutedEvent,
            "EnvelopeExpired": EnvelopeExpiredEvent,
            "GraphNodeExecutionCompleted": GraphNodeExecutionCompletedEvent,
            "GraphNodeExecutionFailed": GraphNodeExecutionFailedEvent,
            "WorkflowCompleted": WorkflowCompletedEvent,
            "WorkflowFailed": WorkflowFailedEvent,
            "GraphNodeExecutionRequested": GraphNodeExecutionRequestedEvent,
            "GraphNodeExecutionStarted": GraphNodeExecutionStartedEvent,
            "GraphNodeExecutionAdvanced": GraphNodeExecutionAdvancedEvent,
            "GraphNodeParallelExecutionRequested": GraphNodeParallelExecutionRequestedEvent,
            "GraphNodeExecutionConditionEvaluated": GraphNodeExecutionConditionEvaluatedEvent,
            "GraphNodeExecutionJoinReady": GraphNodeExecutionJoinReadyEvent,
            "GraphNodeExecutionLoopIteration": GraphNodeExecutionLoopIterationEvent,
            "GraphNodeExecutionTimedOut": GraphNodeExecutionTimedOutEvent,
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
