from datetime import datetime
from typing import Any

from shell_ddd.domain.events.events import DomainEvent, TaskCreated, GraphBuilt, WorkflowStarted, EnvelopeRouted, \
    EnvelopeExpired, NodeCompleted, NodeFailed, WorkflowCompleted, WorkflowFailed, NodeExecutionRequested, NodeStarted, \
    NodeAdvanced


# 1. Tworzymy centralny deserializator z rejestrem Twoich eventów
class EventDeserializer:
    def __init__(self) -> None:
        # Mapowanie nazwy tekstowej (z bazy/szyny) na konkretną klasę
        self._registry: dict[str, type[DomainEvent]] = {
            "TaskCreated": TaskCreated,
            "GraphBuilt": GraphBuilt,
            "WorkflowStarted": WorkflowStarted,
            "EnvelopeRouted": EnvelopeRouted,
            "EnvelopeExpired": EnvelopeExpired,
            "NodeCompleted": NodeCompleted,
            "NodeFailed": NodeFailed,
            "WorkflowCompleted": WorkflowCompleted,
            "WorkflowFailed": WorkflowFailed,
            "NodeExecutionRequested": NodeExecutionRequested,
            "NodeStarted": NodeStarted,
            "NodeAdvanced": NodeAdvanced,
        }

    def deserialize(
            self,
            event_type: str,
            occurred_at: datetime,
            payload: dict[str, Any],
            schema_version: int = 1
    ) -> DomainEvent | None:
        event_cls = self._registry.get(event_type)

        if not event_cls:
            raise NotImplementedError

        try:
            return event_cls.from_payload(
                occurred_at=occurred_at,
                payload=payload,
                schema_version=schema_version
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"Błąd deserializacji eventu {event_type}: {e}")
            return None