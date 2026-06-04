from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_list.internal._assert_single_message_by_status import _assert_single_message_by_status
from shell.component.message.message_status.message_status import MessageStatus


class MessageList:
    """
    Slots:
        _messages — list of messages
    """

    __slots__ = ("_messages",)

    def __init__(self) -> None:
        self._messages: list[Message] | None = None

    @property
    def messages_(self) -> list[Message]:
        if self._messages is None:
            self._messages = []
        return self._messages

    def append_message(self, message: Message) -> None:
        self.messages_.append(message)

    def get_message_by_status(self, status: MessageStatus) -> Message:
        matches = [m for m in self.messages_ if m.status_ == status]
        _assert_single_message_by_status(matches, status)
        return matches[0]
