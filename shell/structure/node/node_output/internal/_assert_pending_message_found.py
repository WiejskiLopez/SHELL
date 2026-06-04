from __future__ import annotations


def _assert_pending_message_found(pending_message) -> None:
    if pending_message is None:
        raise ValueError("[NodeOutput] no PENDING message found in input_message_list")
