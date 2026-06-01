from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.communication_context.communication_context.communication_context import CommunicationContext


def _init_communication_context(
    communication_context: CommunicationContext,
    sender: str,
    receiver: str,
    correlation_id: str = "",
) -> None:
    communication_context._sender = sender
    communication_context._receiver = receiver
    communication_context._correlation_id = correlation_id
    communication_context._previous_messages = []
