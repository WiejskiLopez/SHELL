"""ArchiveEnvelopeHandler — marks an envelope as archived."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.exceptions import EnvelopeNotFound
from shell.domain.execution.value_objects.ids import EnvelopeId

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import ArchiveEnvelopeCommand
    from shell.application.platform.ports.ports import Clock, UnitOfWork


class ArchiveEnvelopeHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: ArchiveEnvelopeCommand) -> None:
        envelope_id = EnvelopeId(command.envelope_id)
        now = self._clock.now()

        async with self._unit_of_work as unit_of_work:
            envelope = await unit_of_work.envelopes.get_by_id(envelope_id)
            if envelope is None:
                raise EnvelopeNotFound(command.envelope_id)

            archive_uri = await unit_of_work.envelope_archive.archive(envelope)
            envelope.archive(archive_uri, now)
            await unit_of_work.envelopes.save(envelope)
