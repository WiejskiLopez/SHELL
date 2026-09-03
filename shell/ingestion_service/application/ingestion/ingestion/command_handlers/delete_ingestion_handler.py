from __future__ import annotations

from typing import TYPE_CHECKING

from shell.ingestion_service.application.ingestion.ingestion.commands.delete_ingestion_command import (
    DeleteIngestionCommand,
)
from shell.ingestion_service.application.ingestion.ingestion.exceptions.ingestion_not_found_error import (
    IngestionNotFoundError,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.repositories.ingestion_repository import (
    IngestionRepository,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
    IngestionId,
)
from shell.platform.application.command_handlers.command_handler import CommandHandler
from shell.platform.domain.value_objects.deleted_at import DeletedAt

if TYPE_CHECKING:
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class DeleteIngestionHandler(CommandHandler[DeleteIngestionCommand]):
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: DeleteIngestionCommand) -> None:
        ingestion_id = IngestionId(command.ingestion_id)
        async with self._unit_of_work as unit_of_work:
            ingestion = await unit_of_work.repository(IngestionRepository).get_by_id(ingestion_id)
            if ingestion is None:
                raise IngestionNotFoundError(f"Ingestion '{command.ingestion_id}' not found")
            now = DeletedAt.from_datetime(self._clock.now())
            ingestion.delete(now)
            await unit_of_work.save(IngestionRepository, ingestion)
