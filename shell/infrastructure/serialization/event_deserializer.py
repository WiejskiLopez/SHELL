from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.events.events import (
    DomainEvent,
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


# 1. Tworzymy centralny deserializator z rejestrem Twoich eventów
class EventDeserializer:
    def __init__(self) -> None:
        # Mapowanie nazwy tekstowej (z bazy/szyny) na konkretną klasę
        self._registry: dict[str, type[DomainEvent]] = {
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

    def deserialize(
        self,
        event_type: str,
        occurred_at: datetime,
        payload: dict[str, Any],
        schema_version: int = 1,
    ) -> DomainEvent | None:
        event_cls = self._registry.get(event_type)

        if not event_cls:
            raise NotImplementedError

        try:
            return event_cls.from_payload(
                occurred_at=occurred_at, payload=payload, schema_version=schema_version
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"Błąd deserializacji eventu {event_type}: {e}")
            return None
