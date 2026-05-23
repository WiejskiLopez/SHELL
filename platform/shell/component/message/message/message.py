from __future__ import annotations

from shell.component.message.message.internal._from_envelope import _from_envelope
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.source_type.source_type import SourceType


class Message:
    """
    Slots:
        _message_envelope — message envelope
        _source_name      — Optional; source name (full path or other identifier)
        _source_type      — Optional; source type
        _status           — Optional; message status
    """

    __slots__ = ("_message_envelope", "_source_name", "_source_type", "_status")

    def __init__(self) -> None:
        self._message_envelope: MessageEnvelope | None = None
        self._source_name: str | None = None
        self._source_type: SourceType | None = None
        self._status: MessageStatus | None = None

    @property
    def message_envelope_(self) -> MessageEnvelope:
        return self._message_envelope

    @property
    def source_name_(self) -> str | None:
        return self._source_name

    @property
    def source_type_(self) -> SourceType | None:
        return self._source_type

    @property
    def status_(self) -> MessageStatus | None:
        return self._status

    @staticmethod
    def from_envelope(envelope: MessageEnvelope, source_name: str, source_type: SourceType) -> Message:
        return _from_envelope(envelope, source_name, source_type)
