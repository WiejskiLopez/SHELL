from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.enabled import Enabled
from shell.domain.platform.value_objects.timestamp import Timestamp
from shell.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
    SchedulerDefinition,
)
from shell.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
    SchedulerJob,
)
from shell.domain.scheduling.value_objects.action_config import ActionConfig
from shell.domain.scheduling.value_objects.batch_size import BatchSize
from shell.domain.scheduling.value_objects.execution_policy import ExecutionPolicy
from shell.domain.scheduling.value_objects.ids import (
    SchedulerDefinitionId,
    SchedulerExecutionId,
)
from shell.domain.scheduling.value_objects.interval_seconds import IntervalSeconds
from shell.domain.scheduling.value_objects.job_name import JobName
from shell.domain.scheduling.value_objects.job_type import JobType
from shell.domain.scheduling.value_objects.scheduler_description import (
    SchedulerDescription,
)
from shell.domain.scheduling.value_objects.scheduler_name import SchedulerName
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
        name=SchedulerName(model.name),
        description=SchedulerDescription(model.description) if model.description else None,
        trigger_config=trigger_config,
        action_config=action_config,
        execution_policy=policy,
        enabled=Enabled(model.enabled),
        created_at=CreatedAt.from_datetime(model.created_at),
        updated_at=Timestamp.from_datetime(model.updated_at),
    )


def scheduler_definition_entity_to_model(
    entity: SchedulerDefinition,
) -> SchedulerDefinitionModel:
    return SchedulerDefinitionModel(
        id=entity.id.value,
        name=entity.name.value,
        description=entity.description.value if entity.description else None,
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
        enabled=entity.enabled.value,
        created_at=entity.created_at.value,
        updated_at=entity.updated_at.value,
    )


def scheduler_execution_model_to_entity(
    model: SchedulerExecutionModel,
) -> SchedulerJob:
    return SchedulerJob(
        id=SchedulerExecutionId(model.id),
        scheduler_definition_id=SchedulerDefinitionId(model.scheduler_definition_id),
        name=JobName(model.name),
        job_type=JobType(model.job_type),
        interval_seconds=IntervalSeconds(model.interval_seconds),
        batch_size=BatchSize(model.batch_size),
        enabled=Enabled(model.enabled),
        config=dict(model.config) if model.config else {},
        created_at=CreatedAt.from_datetime(model.created_at),
        updated_at=Timestamp.from_datetime(model.updated_at),
    )


def scheduler_execution_entity_to_model(
    entity: SchedulerJob,
) -> SchedulerExecutionModel:
    return SchedulerExecutionModel(
        id=entity.id.value,
        scheduler_definition_id=entity.scheduler_definition_id.value,
        name=entity.name.value,
        job_type=entity.job_type.value,
        interval_seconds=entity.interval_seconds.value,
        batch_size=entity.batch_size.value,
        enabled=entity.enabled.value,
        config=entity.config.to_dict(),
        created_at=entity.created_at.value,
        updated_at=entity.updated_at.value,
    )


# ---------------------------------------------------------------------------
# Update (in-place) mappers for optimistic locking
# ---------------------------------------------------------------------------


def scheduler_definition_update_model(model: SchedulerDefinitionModel, entity: SchedulerDefinition) -> None:
    model.name = entity.name.value
    model.description = entity.description.value if entity.description else None
    model.source_context = entity.trigger_config.source_context
    model.trigger_event_type = entity.trigger_config.trigger_event_type
    model.trigger_filter = entity.trigger_config.trigger_filter
    model.action_type = entity.action_config.action_type
    model.action_config = {
        "graph_definition_id": entity.action_config.graph_definition_id,
        "input_mapping": entity.action_config.input_mapping,
        "emit_event_type": entity.action_config.emit_event_type,
        "emit_event_payload": entity.action_config.emit_event_payload,
    }
    model.execution_policy = {
        "max_concurrent": entity.execution_policy.max_concurrent,
        "timeout_seconds": entity.execution_policy.timeout_seconds,
        "retry_count": entity.execution_policy.retry_count,
        "retry_delay_seconds": entity.execution_policy.retry_delay_seconds,
    }
    model.enabled = entity.enabled.value
    model.updated_at = entity.updated_at.value


def scheduler_execution_update_model(model: SchedulerExecutionModel, entity: SchedulerJob) -> None:
    model.scheduler_definition_id = entity.scheduler_definition_id.value
    model.name = entity.name.value
    model.job_type = entity.job_type.value
    model.interval_seconds = entity.interval_seconds.value
    model.batch_size = entity.batch_size.value
    model.enabled = entity.enabled.value
    model.config = entity.config.to_dict()
    model.updated_at = entity.updated_at.value
