from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization import DomainMessageSerializer

if TYPE_CHECKING:
    from datetime import datetime

logger = logging.getLogger(__name__)


class MessageDeserializer:
    def __init__(self, registry: dict[str, type] | None = None) -> None:
        self._registry = registry or {}
        self._serializer = DomainMessageSerializer()

    def deserialize(
        self,
        message_type: str,
        occurred_at: datetime,
        payload: dict[str, object],
        schema_version: int = 1,
    ) -> object | None:
        message_cls = self._registry.get(message_type)

        if not message_cls:
            logger.error("Unknown message type: %s", message_type)
            return None

        try:
            return self._serializer.from_payload(
                message_cls=message_cls,
                occurred_at=occurred_at,
                payload=payload,
                schema_version=schema_version,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error("Failed to deserialize message %s: %s", message_type, e)
            return None
