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
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._clock = clock

    async def handle(self, cmd: ArchiveEnvelopeCommand) -> None:
        envelope_id = EnvelopeId(cmd.envelope_id)
        now = self._clock.now()

        async with self._uow as uow:
            envelope = await uow.envelopes.get_by_id(envelope_id)
            if envelope is None:
                raise EnvelopeNotFound(cmd.envelope_id)

            archive_uri = await uow.envelope_archive.archive(envelope)
            envelope.archive(archive_uri, now)
            await uow.envelopes.save(envelope)
