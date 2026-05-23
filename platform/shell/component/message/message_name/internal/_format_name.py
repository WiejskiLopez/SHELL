from __future__ import annotations

from shell.component.message.message_meta.message_meta import MessageMeta


def _format_name(message_meta: MessageMeta) -> str:
    parts = [
        str(message_meta.session_id_),
        str(message_meta.task_id_),
        str(message_meta.message_id_),
        str(message_meta.sender_node_),
        str(message_meta.target_node_),
        str(message_meta.message_type_.value),
        str(message_meta.status_.value),
        str(message_meta.sequence_id_),
    ]
    return "_".join(parts) + ".json"
