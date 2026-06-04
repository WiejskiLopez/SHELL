from __future__ import annotations

_REQUIRED_FIELDS = (
    "session_id",
    "task_id",
    "message_id",
    "sender_node",
    "target_node",
    "message_type",
    "status",
    "created_at",
    "sequence_id",
    "payload",
)


def _assert_meta_data_fields(data: dict) -> None:
    for field in _REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"[MessageMeta] missing required field '{field}' in meta section")
