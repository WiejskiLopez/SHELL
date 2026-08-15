from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import exists as sa_exists
from sqlalchemy import select

from shell.ingestion.domain.ingestion.aggregates.ingestion.repositories.ingestion_repository import (
    IngestionRepository,
)
from shell.ingestion.infrastructure.ingestion.persistence.sql.mappers.ingestion_entity_to_model import (
    ingestion_entity_to_model,
)
from shell.ingestion.infrastructure.ingestion.persistence.sql.mappers.ingestion_model_to_entity import (
    ingestion_model_to_entity,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

from ..models.ingestion import IngestionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.ingestion.domain.ingestion.aggregates.ingestion.ingestion import (
        Ingestion,
    )
    from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
        IngestionId,
    )


class SqlIngestionRepository(IngestionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, ingestion: Ingestion) -> None:
        model = await self._session.get(IngestionModel, ingestion.id.value)
        if model is None:
            model = ingestion_entity_to_model(ingestion)
            self._session.add(model)
        else:
            model.ingestion_data = ingestion.ingestion_data.value
            model.ingestion_context = ingestion.ingestion_context.value

    async def get_by_id(self, ingestion_id: IngestionId) -> Ingestion | None:
        query = select(IngestionModel).where(IngestionModel.id == ingestion_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ingestion_model_to_entity(row) if row else None

    async def delete(self, id: IngestionId) -> None:
        model = await self._session.get(IngestionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: IngestionId) -> ExistsResult:
        stmt = select(sa_exists().where(IngestionModel.id == id.value))
        result = await self._session.execute(stmt)
        return ExistsResult(result.scalar() or False)
