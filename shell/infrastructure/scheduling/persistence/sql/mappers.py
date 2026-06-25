from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
    SchedulerDefinition,
)
from shell.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
    SchedulerJob,
)
from shell.domain.scheduling.value_objects.action_config import ActionConfig
from shell.domain.scheduling.value_objects.execution_policy import ExecutionPolicy
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
) -> SchedulerJob:
    return SchedulerJob(
        id=SchedulerExecutionId(model.id),
        scheduler_definition_id=SchedulerDefinitionId(model.scheduler_definition_id),
        name=model.name,
        job_type=model.job_type,
        interval_seconds=model.interval_seconds,
        batch_size=model.batch_size,
        enabled=model.enabled,
        config=dict(model.config) if model.config else {},
        created_at=_ensure_utc(model.created_at),
        updated_at=_ensure_utc(model.updated_at),
    )


def scheduler_execution_entity_to_model(
    entity: SchedulerJob,
) -> SchedulerExecutionModel:
    return SchedulerExecutionModel(
        id=entity.id.value,
        scheduler_definition_id=entity.scheduler_definition_id.value,
        name=entity.name,
        job_type=entity.job_type,
        interval_seconds=entity.interval_seconds,
        batch_size=entity.batch_size,
        enabled=entity.enabled,
        config=entity.config,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
