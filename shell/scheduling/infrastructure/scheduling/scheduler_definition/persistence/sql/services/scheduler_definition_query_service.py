from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from sqlalchemy import select

from shell.scheduling.application.scheduling.scheduler_definition.dto.action_config_dto import (
    ActionConfigDto,
)
from shell.scheduling.application.scheduling.scheduler_definition.dto.execution_policy_dto import (
    ExecutionPolicyDto,
)
from shell.scheduling.application.scheduling.scheduler_definition.dto.scheduler_definition import (
    SchedulerDefinitionDto,
)
from shell.scheduling.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
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
            action_config_raw = model.action_config
            action_config = (
                ActionConfigDto(
                    graph_definition_id=cast(
                        "str | None", action_config_raw.get("graph_definition_id")
                    ),
                    input_mapping=(
                        json.dumps(action_config_raw["input_mapping"])
                        if action_config_raw.get("input_mapping")
                        else None
                    ),
                    emit_event_type=cast("str | None", action_config_raw.get("emit_event_type")),
                    emit_event_payload=(
                        json.dumps(action_config_raw["emit_event_payload"])
                        if action_config_raw.get("emit_event_payload")
                        else None
                    ),
                )
                if model.action_config
                else None
            )
            execution_policy_raw = model.execution_policy or {}
            execution_policy = (
                ExecutionPolicyDto(
                    max_concurrent=cast("int", execution_policy_raw.get("max_concurrent", 1)),
                    timeout_seconds=cast("int | None", execution_policy_raw.get("timeout_seconds")),
                    retry_count=cast("int", execution_policy_raw.get("retry_count", 0)),
                    retry_delay_seconds=cast(
                        "int", execution_policy_raw.get("retry_delay_seconds", 0)
                    ),
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
