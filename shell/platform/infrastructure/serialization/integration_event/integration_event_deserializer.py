from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization.errors import SerializationError
from shell.platform.infrastructure.serialization.payload.payload_object_deserializer import (
    PayloadObjectDeserializer,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster

_logger = logging.getLogger(__name__)


class IntegrationEventDeserializer:
    """Deserializes an integration-event envelope into the registered event object.

    The registry maps ``integration_event_name`` to the ``IntegrationEvent`` class.
    An optional upcaster migrates older schema versions before reconstruction.
    """

    def __init__(
        self,
        registry: dict[str, type],
        upcaster: PayloadUpcaster | None = None,
        payload_deserializer: PayloadObjectDeserializer | None = None,
    ) -> None:
        self._registry = registry or {}
        self._upcaster = upcaster
        self._payload_deserializer = payload_deserializer or PayloadObjectDeserializer()

    def deserialize(
        self,
        integration_event_name: str,
        occurred_at: object,
        payload: dict[str, object],
        schema_version: int = 1,
        **envelope_metadata: object,
    ) -> object | None:
        message_cls = self._registry.get(integration_event_name)
        if message_cls is None:
            return None
        try:
            payload, schema_version = self._upcast(integration_event_name, schema_version, payload)
            merged_payload = dict(payload)
            merged_payload.update(
                {name: value for name, value in envelope_metadata.items() if value is not None}
            )
            return self._payload_deserializer.deserialize(
                object_cls=message_cls,
                occurred_at=occurred_at,
                payload=merged_payload,
                schema_version=schema_version,
            )
        except (KeyError, ValueError, TypeError, SerializationError) as exc:
            _logger.error(
                "Failed to deserialize integration event %s: %s", integration_event_name, exc
            )
            return None

    def _upcast(
        self,
        integration_event_name: str,
        schema_version: int,
        payload: dict[str, object],
    ) -> tuple[dict[str, object], int]:
        if self._upcaster is None:
            return payload, schema_version
        upcast_payload, upcast_version = self._upcaster.upcast(
            integration_event_name, schema_version, payload
        )
        return upcast_payload, upcast_version