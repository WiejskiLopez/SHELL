from __future__ import annotations

from shell.component.message.message_meta.internal._assert_meta_data_fields import _assert_meta_data_fields
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_type.message_type import MessageType


def _init_meta_data(meta: object, data: dict) -> None:
    _assert_meta_data_fields(data)

    meta._session_id = data.get("session_id")
    meta._task_id = data.get("task_id")
    meta._parent_task_ids = data.get("parent_task_ids")
    meta._message_id = data.get("message_id")
    meta._parent_message_id = data.get("parent_message_id")
    meta._sender_node = data.get("sender_node")
    meta._target_node = data.get("target_node")
    meta._message_type = MessageType(data["message_type"]) if data.get("message_type") else None
    meta._status = MessageStatus(data["status"]) if data.get("status") else None
    meta._created_at = data.get("created_at")
    meta._sequence_id = data.get("sequence_id")
    meta._payload = data.get("payload")
