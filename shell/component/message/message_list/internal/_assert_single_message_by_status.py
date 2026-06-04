from __future__ import annotations

from shell.component.message.message_status.message_status import MessageStatus


def _assert_single_message_by_status(matches: list, status: MessageStatus) -> None:
    if len(matches) != 1:
        raise ValueError(f"[MessageList] expected exactly one message with status '{status}', found {len(matches)}")
