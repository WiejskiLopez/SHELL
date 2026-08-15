from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.ingestion.domain.ingestion.aggregates.ingestion.events.ingestion_created_event import (
    IngestionCreatedEvent,
)
from shell.ingestion.domain.ingestion.aggregates.ingestion.events.ingestion_deleted_event import (
    IngestionDeletedEvent,
)
from shell.ingestion.domain.ingestion.aggregates.ingestion.events.ingestion_updated_event import (
    IngestionUpdatedEvent,
)
from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
    IngestionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt

if TYPE_CHECKING:
    from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_context import (
        IngestionContext,
    )
    from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_data import (
        IngestionData,
    )


class Ingestion(AggregateRoot[IngestionId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_ingestion_data",
        "_ingestion_context",
    )

    _ingestion_data: IngestionData
    _ingestion_context: IngestionContext
    _created_at: CreatedAt
    _updated_at: UpdatedAt

    def __init__(
        self,
        *,
        id: IngestionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        ingestion_data: IngestionData,
        ingestion_context: IngestionContext,
    ) -> None:
        super().__init__(id)
        self._ingestion_data = ingestion_data
        self._ingestion_context = ingestion_context
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: IngestionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        ingestion_data: IngestionData,
        ingestion_context: IngestionContext,
    ) -> Self:
        return cls(
            id=id,
            ingestion_data=ingestion_data,
            ingestion_context=ingestion_context,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    def update(self, now: UpdatedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Ingestion already deleted")
        self._updated_at = now
        self.append_event(
            IngestionUpdatedEvent.now(
                ingestion_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            IngestionUpdatedEvent.now(
                ingestion_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def delete(self, now: DeletedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Ingestion already deleted")
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            IngestionDeletedEvent.now(
                ingestion_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            IngestionDeletedEvent.now(
                ingestion_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def ingestion_data(self) -> IngestionData:
        return self._ingestion_data

    @property
    def ingestion_context(self) -> IngestionContext:
        return self._ingestion_context

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt:
        return self._updated_at

    @classmethod
    def _new(
        cls,
        *,
        id_: IngestionId,
        now: OccurredAt,
        ingestion_data: IngestionData,
        ingestion_context: IngestionContext,
    ) -> Ingestion:
        instance = cls(
            id=id_,
            ingestion_data=ingestion_data,
            ingestion_context=ingestion_context,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            IngestionCreatedEvent.now(
                ingestion_id=instance.id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    @classmethod
    def new(
        cls,
        *,
        id_: IngestionId,
        ingestion_data: IngestionData,
        ingestion_context: IngestionContext,
        now: CreatedAt,
    ) -> Ingestion:
        return cls._new(
            id_=id_,
            ingestion_data=ingestion_data,
            ingestion_context=ingestion_context,
            now=OccurredAt.from_datetime(now.value),
        )
