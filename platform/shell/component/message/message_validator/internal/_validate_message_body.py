from __future__ import annotations

from shell.component.message.message_validator.internal._assert_message_body_valid import _assert_message_body_valid


def _validate_message_body(body: str) -> None:
    _assert_message_body_valid(body)
