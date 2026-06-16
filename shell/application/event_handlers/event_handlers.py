"""Application-level event handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.ports.ports import Clock, Logger, UnitOfWork
    from shell.domain.events.events import DomainEvent, EnvelopeRouted


class ArchiveOnDeliveredHandler:
    """Subscribes to EnvelopeRouted and archives the envelope when it reaches DELIVERED stage."""

    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def handle(self, event: EnvelopeRouted) -> None:
        from shell.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
        from shell.domain.value_objects.ids import EnvelopeId

        async with self._uow as uow:
            envelope = await uow.envelopes.get_by_id(EnvelopeId(event.envelope_id.value))
            if envelope is None:
                return
            if envelope.status != EnvelopeStatus.DELIVERED:
                return
            archive_uri = await uow.envelope_archive.archive(envelope)
            envelope.archive_uri = archive_uri
            envelope.transition_stage(EnvelopeStage.ARCHIVED, self._clock.now())
            await uow.envelopes.save(envelope)
            await uow.commit()


class LogAuditHandler:
    """Subscribes to all domain events and logs them for audit purposes."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def handle(self, event: DomainEvent) -> None:
        self._logger.info(
            "domain_event",
            event_type=type(event).__name__,
            occurred_at=str(event.occurred_at),
        )
