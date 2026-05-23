from __future__ import annotations


def _assert_message_body_valid(body: str) -> None:
    import yaml

    if not body or not body.strip():
        raise ValueError("[MessageValidator] message body is empty")

    try:
        data = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise ValueError(f"[MessageValidator] message body is not valid YAML: {error}")

    if not isinstance(data, dict):
        raise ValueError(f"[MessageValidator] message body must be a YAML mapping, got {type(data).__name__}")

    if "meta" not in data:
        raise ValueError("[MessageValidator] message body is missing required section 'meta'")

    if "payload" not in data:
        raise ValueError("[MessageValidator] message body is missing required field 'payload'")

    meta = data["meta"]
    if not isinstance(meta, dict):
        raise ValueError(f"[MessageValidator] 'meta' must be a mapping, got {type(meta).__name__}")

    _REQUIRED_META_FIELDS = (
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
    for field in _REQUIRED_META_FIELDS:
        if field not in meta:
            raise ValueError(f"[MessageValidator] meta is missing required field '{field}'")
