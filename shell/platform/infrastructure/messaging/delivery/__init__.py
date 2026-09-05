"""Shared delivery primitives for outbox/inbox transports."""

from __future__ import annotations

from shell.platform.infrastructure.messaging.delivery.inbox_processor_base import (
    InboxProcessorBase,
)
from shell.platform.infrastructure.messaging.delivery.outbox_relay_base import (
    OutboxRelayBase,
)

__all__ = ["InboxProcessorBase", "OutboxRelayBase"]