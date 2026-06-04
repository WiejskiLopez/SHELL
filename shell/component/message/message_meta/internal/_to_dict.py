from __future__ import annotations


def _to_dict(meta: object) -> dict:
    return {
        "session_id": meta.session_id_,
        "task_id": meta.task_id_,
        "parent_task_ids": meta.parent_task_ids_,
        "message_id": meta.message_id_,
        "parent_message_id": meta.parent_message_id_,
        "sender_node": meta.sender_node_,
        "target_node": meta.target_node_,
        "message_type": meta.message_type_.value if meta.message_type_ else None,
        "status": meta.status_.value if meta.status_ else None,
        "created_at": meta.created_at_,
        "sequence_id": meta.sequence_id_,
        "payload": meta.payload_,
    }
