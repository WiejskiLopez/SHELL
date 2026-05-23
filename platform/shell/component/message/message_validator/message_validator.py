from __future__ import annotations

from shell.component.message.message_validator.internal._is_valid_message import _is_valid_message
from shell.component.message.message_validator.internal._validate_message_body import _validate_message_body


class MessageValidator:

    @staticmethod
    def validate_message_body(body: str) -> None:
        _validate_message_body(body)

    @staticmethod
    def is_valid_message(body: str) -> bool:
        return _is_valid_message(body)
