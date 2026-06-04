from __future__ import annotations


def _assert_response_type_mapped(response_type, message_type) -> None:
    if response_type is None:
        raise ValueError(f"[MessageMeta] no response mapping for message_type: '{message_type}'")
