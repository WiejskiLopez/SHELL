from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.scheduling.scheduler_definition.dto.action_config_dto import (
    ActionConfigDto,
)
from shell.application.scheduling.scheduler_definition.dto.execution_policy_dto import (
    ExecutionPolicyDto,
)
from shell.application.scheduling.scheduler_definition.dto.scheduler_definition import (
    SchedulerDefinitionDto,
)
from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SchedulerDefinitionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, scheduler_definition_id: str) -> SchedulerDefinitionDto | None:
        async with self._session_factory() as session:
            stmt = select(SchedulerDefinitionModel).where(
                SchedulerDefinitionModel.id == scheduler_definition_id
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            action_config = (
                ActionConfigDto(
                    graph_definition_id=model.action_config.get("graph_definition_id"),
                    input_mapping=(
                        json.dumps(model.action_config["input_mapping"])
                        if model.action_config.get("input_mapping")
                        else None
                    ),
                    emit_event_type=model.action_config.get("emit_event_type"),
                    emit_event_payload=(
                        json.dumps(model.action_config["emit_event_payload"])
                        if model.action_config.get("emit_event_payload")
                        else None
                    ),
                )
                if model.action_config
                else None
            )
            execution_policy = (
                ExecutionPolicyDto(
                    **(model.execution_policy or {}),
                )
                if model.execution_policy
                else None
            )
            return SchedulerDefinitionDto(
                id=model.id,
                name=model.name,
                description=model.description,
                source_context=model.source_context,
                trigger_event_type=model.trigger_event_type,
                trigger_filter=(json.dumps(model.trigger_filter) if model.trigger_filter else None),
                action_type=model.action_type,
                action_config=action_config,
                execution_policy=execution_policy,
                enabled=model.enabled,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
