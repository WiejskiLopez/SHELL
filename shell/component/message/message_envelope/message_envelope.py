from __future__ import annotations

from shell.component.message.message_envelope.internal._from_meta_and_payload import _from_meta_and_payload
from shell.component.message.message_envelope.internal._init_envelope_data import _init_envelope_data
from shell.component.message.message_envelope.internal._to_dict import _to_dict
from shell.component.message.message_meta.message_meta import MessageMeta


class MessageEnvelope:
    """
    Slots:
        _message_meta — message metadata
        _payload      — message payload
    """

    __slots__ = ("_message_meta", "_payload")

    def __init__(self) -> None:
        self._message_meta: MessageMeta | None = None
        self._payload: str | None = None

    @property
    def message_meta_(self) -> MessageMeta:
        return self._message_meta

    @property
    def payload_(self) -> str:
        return self._payload

    def init_envelope_data(self, data: dict) -> None:
        _init_envelope_data(self, data)

    def to_dict(self) -> dict:
        return _to_dict(self)

    @staticmethod
    def from_meta_and_payload(message_meta: MessageMeta, payload: str) -> MessageEnvelope:
        return _from_meta_and_payload(message_meta, payload)
