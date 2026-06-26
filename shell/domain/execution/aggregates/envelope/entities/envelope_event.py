from __future__ import annotations

from shell.domain.execution.aggregates.envelope.value_objects.envelope_event_id import (
    EnvelopeEventId,
)
from shell.domain.execution.aggregates.envelope.value_objects.envelope_event_kind import (
    EnvelopeEventKind,
)
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.platform.base.entity import Entity
from shell.domain.platform.value_objects.created_at import CreatedAt


class EnvelopeEvent(Entity[EnvelopeEventId]):
    __slots__ = ("_kind", "_payload", "_created_at")

    def __init__(
        self,
        id: EnvelopeEventId,
        kind: EnvelopeEventKind,
        payload: StateData,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._kind = kind
        self._payload = payload
        self._created_at = created_at

    @property
    def kind(self) -> EnvelopeEventKind:
        return self._kind

    @property
    def payload(self) -> StateData:
        return self._payload

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at
