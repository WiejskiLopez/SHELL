from __future__ import annotations

from typing import TYPE_CHECKING

from shell.ingestion.infrastructure.ingestion.persistence.sql.models.ingestion import (
    IngestionModel,
)

if TYPE_CHECKING:
    from shell.ingestion.domain.ingestion.aggregates.ingestion.ingestion import (
        Ingestion,
    )


def ingestion_entity_to_model(ingestion: Ingestion) -> IngestionModel:
    return IngestionModel(
        id=ingestion.id.value,
        ingestion_data=ingestion.ingestion_data.value,
        ingestion_context=ingestion.ingestion_context.value,
        created_at=ingestion.created_at.value if ingestion.created_at else None,
        updated_at=ingestion.updated_at.value,
        deleted_at=ingestion._deleted_at.value if ingestion._deleted_at is not None else None,
    )
