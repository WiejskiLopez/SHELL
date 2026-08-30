from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.ingestion_service.domain.ingestion.aggregates.ingestion.ingestion import (
        Ingestion,
    )
    from shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.ingestion import (
        IngestionModel,
    )


def ingestion_change_model(model: IngestionModel, entity: Ingestion) -> None:
    model.ingestion_data = entity.ingestion_data.value
    model.ingestion_context = entity.ingestion_context.value
    assert entity.created_at is not None
    model.created_at = entity.created_at.value
    model.changed_at = entity.changed_at.value
    model.deleted_at = entity.deleted_at.value
