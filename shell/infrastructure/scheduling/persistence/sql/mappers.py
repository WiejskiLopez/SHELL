from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from shell.domain.scheduling.aggregates.scheduler_definition import (
    SchedulerDefinition,
)
from shell.domain.scheduling.aggregates.scheduler_execution import (
    SchedulerExecution,
)
from shell.domain.scheduling.value_objects.action_config import ActionConfig
from shell.domain.scheduling.value_objects.execution_policy import ExecutionPolicy
from shell.domain.scheduling.value_objects.execution_status import ExecutionStatus
from shell.domain.scheduling.value_objects.ids import (
    SchedulerDefinitionId,
    SchedulerExecutionId,
)
from shell.domain.scheduling.value_objects.trigger_config import TriggerConfig
from shell.infrastructure.scheduling.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)
from shell.infrastructure.scheduling.persistence.sql.models.scheduler_execution import (
    SchedulerExecutionModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def scheduler_definition_model_to_entity(
    model: SchedulerDefinitionModel,
) -> SchedulerDefinition:
    trigger_config = TriggerConfig(
        source_context=model.source_context,
        trigger_event_type=model.trigger_event_type,
        trigger_filter=dict(model.trigger_filter) if model.trigger_filter else None,
    )
    action_config = ActionConfig(
        action_type=model.action_type,
        **{k: v for k, v in (model.action_config or {}).items() if k != "action_type"},
    )
    policy = ExecutionPolicy(
        **(model.execution_policy or {}),
    )
    return SchedulerDefinition(
        id=SchedulerDefinitionId(model.id),
        name=model.name,
        description=model.description,
        trigger_config=trigger_config,
        action_config=action_config,
        execution_policy=policy,
        enabled=model.enabled,
        created_at=_ensure_utc(model.created_at),
        updated_at=_ensure_utc(model.updated_at),
    )


def scheduler_definition_entity_to_model(
    entity: SchedulerDefinition,
) -> SchedulerDefinitionModel:
    return SchedulerDefinitionModel(
        id=entity.id.value,
        name=entity.name,
        description=entity.description,
        source_context=entity.trigger_config.source_context,
        trigger_event_type=entity.trigger_config.trigger_event_type,
        trigger_filter=entity.trigger_config.trigger_filter,
        action_type=entity.action_config.action_type,
        action_config={
            "graph_definition_id": entity.action_config.graph_definition_id,
            "input_mapping": entity.action_config.input_mapping,
            "emit_event_type": entity.action_config.emit_event_type,
            "emit_event_payload": entity.action_config.emit_event_payload,
        },
        execution_policy={
            "max_concurrent": entity.execution_policy.max_concurrent,
            "timeout_seconds": entity.execution_policy.timeout_seconds,
            "retry_count": entity.execution_policy.retry_count,
            "retry_delay_seconds": entity.execution_policy.retry_delay_seconds,
        },
        enabled=entity.enabled,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def scheduler_execution_model_to_entity(
    model: SchedulerExecutionModel,
) -> SchedulerExecution:
    return SchedulerExecution(
        id=SchedulerExecutionId(model.id),
        scheduler_definition_id=SchedulerDefinitionId(model.scheduler_definition_id),
        status=ExecutionStatus(model.status),
        trigger_event_id=model.trigger_event_id,
        trigger_event_type=model.trigger_event_type,
        action_ref=model.action_ref,
        action_ref_type=model.action_ref_type,
        input_state=dict(model.input_state) if model.input_state else {},
        output_state=dict(model.output_state) if model.output_state else {},
        error=model.error,
        started_at=_ensure_utc(model.started_at) if model.started_at else None,
        completed_at=_ensure_utc(model.completed_at) if model.completed_at else None,
        created_at=_ensure_utc(model.created_at),
        updated_at=_ensure_utc(model.updated_at),
    )


def scheduler_execution_entity_to_model(
    entity: SchedulerExecution,
) -> SchedulerExecutionModel:
    return SchedulerExecutionModel(
        id=entity.id.value,
        scheduler_definition_id=entity.scheduler_definition_id.value,
        status=entity.status.value,
        trigger_event_id=entity.trigger_event_id,
        trigger_event_type=entity.trigger_event_type,
        action_ref=entity.action_ref,
        action_ref_type=entity.action_ref_type,
        input_state=entity.input_state,
        output_state=entity.output_state,
        error=entity.error,
        started_at=entity.started_at,
        completed_at=entity.completed_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
