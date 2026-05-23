from __future__ import annotations

from shell.component.message.message_meta.internal._init_meta_data import _init_meta_data
from shell.component.message.message_meta.internal._reverse_message_meta import _reverse_message_meta
from shell.component.message.message_meta.internal._to_dict import _to_dict
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_type.message_type import MessageType


class MessageMeta:
    """
    Slots:
        _session_id        — session identifier
        _task_id           — task identifier
        _parent_task_ids   — Optional; list of parent task identifiers
        _message_id        — message identifier
        _parent_message_id — Optional; parent message identifier
        _sender_node       — sender node name
        _target_node       — target node name
        _message_type      — message type
        _status            — message status
        _created_at        — creation timestamp
        _sequence_id       — sequence number
        _payload           — message payload
    """

    __slots__ = (
        "_session_id",
        "_task_id",
        "_parent_task_ids",
        "_message_id",
        "_parent_message_id",
        "_sender_node",
        "_target_node",
        "_message_type",
        "_status",
        "_created_at",
        "_sequence_id",
        "_payload",
    )

    def __init__(self) -> None:
        self._session_id: str | None = None
        self._task_id: str | None = None
        self._parent_task_ids: list[str] | None = None
        self._message_id: str | None = None
        self._parent_message_id: str | None = None
        self._sender_node: str | None = None
        self._target_node: str | None = None
        self._message_type: MessageType | None = None
        self._status: MessageStatus | None = None
        self._created_at: str | None = None
        self._sequence_id: int | None = None
        self._payload: str | None = None

    @property
    def session_id_(self) -> str:
        return self._session_id

    @property
    def task_id_(self) -> str:
        return self._task_id

    @property
    def parent_task_ids_(self) -> list[str] | None:
        return self._parent_task_ids

    @property
    def message_id_(self) -> str:
        return self._message_id

    @property
    def parent_message_id_(self) -> str | None:
        return self._parent_message_id

    @property
    def sender_node_(self) -> str:
        return self._sender_node

    @property
    def target_node_(self) -> str:
        return self._target_node

    @property
    def message_type_(self) -> MessageType:
        return self._message_type

    @property
    def status_(self) -> MessageStatus:
        return self._status

    @property
    def created_at_(self) -> str:
        return self._created_at

    @property
    def sequence_id_(self) -> int:
        return self._sequence_id

    @property
    def payload_(self) -> str:
        return self._payload

    def init_meta_data(self, data: dict) -> None:
        _init_meta_data(self, data)

    def to_dict(self) -> dict:
        return _to_dict(self)

    @staticmethod
    def reverse_message_meta(input_meta: MessageMeta) -> MessageMeta:
        return _reverse_message_meta(input_meta)
