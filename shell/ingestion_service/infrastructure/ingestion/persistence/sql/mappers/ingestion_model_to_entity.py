from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.ingestion_service.domain.ingestion.aggregates.ingestion.ingestion import Ingestion
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

if TYPE_CHECKING:
    from shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.ingestion import (
        IngestionModel,
    )


def ingestion_model_to_entity(model: IngestionModel) -> Ingestion:
    def _utc(dt: datetime) -> datetime:
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt

    return Ingestion.restore(
        id=IngestionId(model.id),
        ingestion_data=IngestionData(model.ingestion_data),
        ingestion_context=IngestionContext(model.ingestion_context),
        created_at=CreatedAt.from_datetime(_utc(model.created_at)),
    )
