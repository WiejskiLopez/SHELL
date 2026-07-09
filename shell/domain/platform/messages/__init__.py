"""Platform shared kernel — Message base class for inter-aggregate communication."""

from shell.domain.platform.messages.message import Message
from shell.domain.platform.messages.value_objects import MessageData, MessageId

__all__ = [
    "Message",
    "MessageData",
    "MessageId",
]
