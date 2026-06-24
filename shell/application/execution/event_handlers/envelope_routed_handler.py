"""Subscribes to EnvelopeRoutedEvent and archives the envelope when it reaches DELIVERED stage."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.ports.ports import Clock, UnitOfWork
    from shell.domain.execution.events import EnvelopeRoutedEvent


class ArchiveOnDeliveredHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, event: EnvelopeRoutedEvent) -> None:
        from shell.domain.execution.value_objects.ids import EnvelopeId
        from shell.domain.platform.value_objects.envelope_status import EnvelopeStatus

        async with self._unit_of_work as unit_of_work:
            envelope = await unit_of_work.envelopes.get_by_id(EnvelopeId(event.envelope_id.value))
            if envelope is None:
                return
            if envelope.status != EnvelopeStatus.DELIVERED:
                return
            archive_uri = await unit_of_work.envelope_archive.archive(envelope)
            envelope.archive(archive_uri, self._clock.now())
            await unit_of_work.envelopes.save(envelope)
