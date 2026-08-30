from __future__ import annotations

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
from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import ensure_utc

if TYPE_CHECKING:
    from shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.ingestion import (
        IngestionModel,
    )


def ingestion_model_to_entity(model: IngestionModel) -> Ingestion:
    return Ingestion.restore(
        id=IngestionId(model.id),
        ingestion_data=IngestionData(model.ingestion_data),
        ingestion_context=IngestionContext(model.ingestion_context),
        created_at=CreatedAt.from_datetime(ensure_utc(model.created_at)),
        changed_at=ChangedAt.from_datetime(ensure_utc(model.changed_at))
        if model.changed_at
        else ChangedAt.none(),
        deleted_at=DeletedAt.from_datetime(ensure_utc(model.deleted_at))
        if model.deleted_at
        else DeletedAt.none(),
    )
