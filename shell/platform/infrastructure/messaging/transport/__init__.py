"""Transport adapters for delivering DeliveryEnvelope records between bounded contexts."""

from __future__ import annotations

from shell.platform.infrastructure.messaging.transport.envelope_codec import EnvelopeCodec
from shell.platform.infrastructure.messaging.transport.outbox_to_transport_relay import (
    OutboxToTransportRelay,
)

__all__ = [
    "EnvelopeCodec",
    "OutboxToTransportRelay",
]
