from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from datetime import datetime

    from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster

logger = logging.getLogger(__name__)


class EventDeserializer:
    def __init__(
        self,
        registry: dict[str, type] | None = None,
        upcaster: PayloadUpcaster | None = None,
    ) -> None:
        self._registry = registry or {}
        self._upcaster = upcaster
        self._serializer = DomainEventSerializer()

    def deserialize(
        self,
        event_type: str,
        occurred_at: datetime,
        payload: dict[str, object],
        schema_version: int = 1,
    ) -> object | None:
        event_cls = self._registry.get(event_type)

        if not event_cls:
            logger.error("Unknown event type: %s", event_type)
            return None

        try:
            if self._upcaster is not None:
                payload, schema_version = self._upcaster.upcast(
                    event_type,
                    schema_version,
                    payload,
                )
            return self._serializer.from_payload(
                event_cls=event_cls,
                occurred_at=occurred_at,
                payload=payload,
                schema_version=schema_version,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error("Failed to deserialize event %s: %s", event_type, e)
            return None
