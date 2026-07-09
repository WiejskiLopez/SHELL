from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shell.domain.platform.messages.value_objects.message_data import MessageData
from shell.domain.platform.messages.value_objects.message_id import MessageId

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class Message:
    message_id: MessageId = field(default_factory=MessageId.generate)
    created_at: CreatedAt
    message_data: MessageData = field(default_factory=MessageData)
