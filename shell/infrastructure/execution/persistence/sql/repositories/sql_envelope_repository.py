from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.envelope.repositories.envelope_repository import (
    EnvelopeRepository,
)
from shell.domain.execution.value_objects.ids import (  # noqa: TC002 — EnvelopeId i WorkflowId używane w konstruktorach w repozytorium
    EnvelopeId,
    WorkflowId,
)
from shell.domain.platform.value_objects.envelope_status import EnvelopeStatus
from shell.infrastructure.platform.persistence.sql.mappers import (
    envelope_entity_to_model,
    envelope_model_to_entity,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models import EnvelopeModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.envelope import Envelope
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlEnvelopeRepository(EnvelopeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None:
        query = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(EnvelopeModel.id == envelope_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return envelope_model_to_entity(row) if row else None

    async def save(self, envelope: Envelope) -> None:
        model = envelope_entity_to_model(envelope)
        await self._session.merge(model)

    async def list_by_workflow(
        self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0
    ) -> list[Envelope]:
        query = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(EnvelopeModel.workflow_id == workflow_id.value)
            .offset(offset)
        )
        if limit is not None:
            query = query.limit(limit)
        rows = (await self._session.execute(query)).scalars().all()
        return [envelope_model_to_entity(row) for row in rows]

    async def list_pending(
        self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0
    ) -> list[Envelope]:
        query = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(
                EnvelopeModel.workflow_id == workflow_id.value,
                EnvelopeModel.status == EnvelopeStatus.PENDING.value,
            )
            .offset(offset)
        )
        if limit is not None:
            query = query.limit(limit)
        rows = (await self._session.execute(query)).scalars().all()
        return [envelope_model_to_entity(row) for row in rows]


__all__ = [
    "EnvelopeModel",
    "SqlEnvelopeRepository",
    "select",
    "selectinload",
]
