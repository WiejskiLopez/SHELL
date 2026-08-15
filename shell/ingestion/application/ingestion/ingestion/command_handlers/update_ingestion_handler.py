from __future__ import annotations

from typing import TYPE_CHECKING

from shell.ingestion.domain.ingestion.aggregates.ingestion.repositories.ingestion_repository import (
    IngestionRepository,
)
from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
    IngestionId,
)
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.ingestion.application.ingestion.ingestion.commands.update_ingestion_command import (
        UpdateIngestionCommand,
    )
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class IngestionNotFoundError(Exception):
    pass


class UpdateIngestionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: UpdateIngestionCommand) -> None:
        ingestion_id = IngestionId(command.ingestion_id)
        async with self._unit_of_work as unit_of_work:
            ingestion = await unit_of_work.repository(IngestionRepository).get_by_id(ingestion_id)
            if ingestion is None:
                raise IngestionNotFoundError(f"Ingestion '{command.ingestion_id}' not found")
            now = UpdatedAt.from_datetime(self._clock.now())
            ingestion.update(now)
            await unit_of_work.save(IngestionRepository, ingestion)
