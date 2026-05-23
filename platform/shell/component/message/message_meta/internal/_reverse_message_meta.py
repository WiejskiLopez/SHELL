from __future__ import annotations

from datetime import datetime, timezone

from shell.component.message.message_meta.internal._assert_response_type_mapped import _assert_response_type_mapped
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_type.message_type import MessageType

_RESPONSE_TYPE_MAP = {
    MessageType.EVENT: MessageType.ACK,
    MessageType.COMMAND: MessageType.EXECUTED,
    MessageType.REQUEST: MessageType.RESPONSE,
    MessageType.RESPONSE: MessageType.OK,
    MessageType.ACK: MessageType.OK,
}


def _reverse_message_meta(input_meta: object) -> object:
    from shell.component.message.message_meta.message_meta import MessageMeta

    response_type = _RESPONSE_TYPE_MAP.get(input_meta.message_type_)
    _assert_response_type_mapped(response_type, input_meta.message_type_)

    now = datetime.now(timezone.utc).isoformat()

    meta = MessageMeta()
    meta._session_id = input_meta.session_id_
    meta._task_id = input_meta.task_id_
    meta._parent_task_ids = input_meta.parent_task_ids_
    meta._message_id = now
    meta._parent_message_id = input_meta.message_id_
    meta._sender_node = input_meta.target_node_
    meta._target_node = input_meta.sender_node_
    meta._message_type = response_type
    meta._status = MessageStatus.PENDING
    meta._created_at = now
    meta._sequence_id = (input_meta.sequence_id_ or 0) + 1
    meta._payload = None

    return meta
