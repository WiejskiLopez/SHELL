"""RoutableMessage — concrete message produced by the MessageRouter aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_data import (  # noqa: TC001 -- needed at runtime for deserialization type resolution
    MessageData,
)
from shell.platform.domain.messages import DomainMessage


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutableMessage(DomainMessage):
    message_data: MessageData
