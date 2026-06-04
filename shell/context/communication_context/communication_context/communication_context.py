"""communication_context.py
CommunicationContext — inter-agent communication context.

Slots:
    _sender          — identifier of the sending agent
    _receiver        — identifier of the receiving agent
    _correlation_id  — correlation ID linking delegations in a conversation
    _previous_messages — list of previous messages in this conversation
"""

from __future__ import annotations

from shell.context.communication_context.communication_context.internal._init_communication_context import _init_communication_context


class CommunicationContext:
    """Inter-agent communication context.

    Slots:
        _sender          — identifier of the sending agent
        _receiver        — identifier of the receiving agent
        _correlation_id  — correlation ID linking delegations in a conversation
        _previous_messages — list of previous messages in this conversation
    """

    __slots__ = ("_sender", "_receiver", "_correlation_id", "_previous_messages")

    def __init__(self) -> None:
        self._sender: str = ""
        self._receiver: str = ""
        self._correlation_id: str = ""
        self._previous_messages: list[dict] = []

    @property
    def sender_(self) -> str:
        return self._sender

    @property
    def receiver_(self) -> str:
        return self._receiver

    @property
    def correlation_id_(self) -> str:
        return self._correlation_id

    @property
    def previous_messages_(self) -> list[dict]:
        return self._previous_messages

    def init_communication_context(self, sender: str, receiver: str, correlation_id: str = "") -> None:
        _init_communication_context(self, sender=sender, receiver=receiver, correlation_id=correlation_id)
