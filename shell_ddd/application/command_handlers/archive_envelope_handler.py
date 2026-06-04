"""ArchiveEnvelopeHandler — marks an envelope as archived."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.exceptions import EnvelopeNotFound
from shell_ddd.domain.value_objects.envelope_status import EnvelopeStage
from shell_ddd.domain.value_objects.ids import EnvelopeId

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import ArchiveEnvelopeCommand
    from shell_ddd.application.ports.ports import Clock, EventPublisher, UnitOfWork


class ArchiveEnvelopeHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        events: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._events = events

    async def handle(self, cmd: ArchiveEnvelopeCommand) -> None:
        env_id = EnvelopeId(cmd.envelope_id)
        now = self._clock.now()

        async with self._uow as uow:
            envelope = await uow.envelopes.get_by_id(env_id)
            if envelope is None:
                raise EnvelopeNotFound(cmd.envelope_id)

            archive_uri = await uow.envelope_archive.archive(envelope)
            envelope.archive_uri = archive_uri
            envelope.transition_stage(EnvelopeStage.ARCHIVED, now)
            await uow.envelopes.save(envelope)
            await uow.commit()
