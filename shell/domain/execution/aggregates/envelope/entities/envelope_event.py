from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.envelope.value_objects.ids.envelope_event_id import EnvelopeEventId
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime


class EnvelopeEvent(Entity[EnvelopeEventId]):
    __slots__ = ("kind", "payload", "created_at")

    def __init__(
        self,
        id: EnvelopeEventId,
        kind: str,
        payload: dict[str, object],
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self.kind = kind
        self.payload = payload
        self.created_at = created_at
