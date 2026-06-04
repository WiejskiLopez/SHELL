from __future__ import annotations

from shell.component.message.message_validator.internal._assert_message_body_valid import _assert_message_body_valid


def _is_valid_message(body: str) -> bool:
    try:
        _assert_message_body_valid(body)
        return True
    except (ValueError, Exception):
        return False
