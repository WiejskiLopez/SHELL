from __future__ import annotations

from typing import TYPE_CHECKING

from shell.ingestion_service.domain.ingestion.aggregates.ingestion.ingestion import Ingestion
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.repositories.ingestion_repository import (
    IngestionRepository,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_context import (
    IngestionContext,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_data import (
    IngestionData,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
    IngestionId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from shell.ingestion_service.application.ingestion.ingestion.commands.create_ingestion_command import (
        CreateIngestionCommand,
    )
    from shell.platform.application.ports.identity import IdGenerator
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class CreateIngestionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateIngestionCommand) -> str:
        now = CreatedAt.from_datetime(self._clock.now())
        ingestion_id = self._id_generator.new_id(IngestionId)
        ingestion = Ingestion.new(
            id_=ingestion_id,
            ingestion_data=IngestionData(JsonStr(command.ingestion_data)),
            ingestion_context=IngestionContext(JsonStr(command.ingestion_context)),
            now=now,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(IngestionRepository, ingestion)
        return ingestion_id.value
