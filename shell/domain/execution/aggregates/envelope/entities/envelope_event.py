from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.envelope.value_objects.envelope_event_id import (
    EnvelopeEventId,
)
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime


class EnvelopeEvent(Entity[EnvelopeEventId]):
    __slots__ = ("_kind", "_payload", "_created_at")

    def __init__(
        self,
        id: EnvelopeEventId,
        kind: str,
        payload: dict[str, object],
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self._kind = kind
        self._payload = payload
        self._created_at = created_at

    @property
    def kind(self) -> str:
        return self._kind

    @property
    def payload(self) -> dict[str, object]:
        return dict(self._payload)

    @property
    def created_at(self) -> datetime:
        return self._created_at
