import json
from datetime import UTC, datetime

from shell.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
    SchedulerDefinition,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.action_config import (
    ActionConfig,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.execution_policy import (
    ExecutionPolicy,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_description import (
    SchedulerDescription,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_name import (
    SchedulerName,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.trigger_config import (
    TriggerConfig,
)
from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.enabled import Enabled
from shell.platform.domain.value_objects.timestamp import Timestamp
from shell.platform.types import JsonStr


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
        trigger_filter=JsonStr(json.dumps(dict(model.trigger_filter))) if model.trigger_filter else None,
    )
    action_config = ActionConfig(
        action_type=model.action_type,
        graph_definition_id=model.action_config.get("graph_definition_id"),
        input_mapping=JsonStr(json.dumps(model.action_config.get("input_mapping"))) if model.action_config.get("input_mapping") else None,
        emit_event_type=model.action_config.get("emit_event_type"),
        emit_event_payload=JsonStr(json.dumps(model.action_config.get("emit_event_payload"))) if model.action_config.get("emit_event_payload") else None,
    )
    policy = ExecutionPolicy(
        **(model.execution_policy or {}),
    )
    return SchedulerDefinition.restore(
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
        trigger_filter=json.loads(entity.trigger_config.trigger_filter.value) if entity.trigger_config.trigger_filter else None,
        action_type=entity.action_config.action_type,
        action_config={
            "graph_definition_id": entity.action_config.graph_definition_id,
            "input_mapping": json.loads(entity.action_config.input_mapping.value) if entity.action_config.input_mapping else None,
            "emit_event_type": entity.action_config.emit_event_type,
            "emit_event_payload": json.loads(entity.action_config.emit_event_payload.value) if entity.action_config.emit_event_payload else None,
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


def scheduler_definition_update_model(
    model: SchedulerDefinitionModel, entity: SchedulerDefinition
) -> None:
    model.name = entity.name.value
    model.description = entity.description.value if entity.description else None
    model.source_context = entity.trigger_config.source_context
    model.trigger_event_type = entity.trigger_config.trigger_event_type
    model.trigger_filter = json.loads(entity.trigger_config.trigger_filter.value) if entity.trigger_config.trigger_filter else None
    model.action_type = entity.action_config.action_type
    model.action_config = {
        "graph_definition_id": entity.action_config.graph_definition_id,
        "input_mapping": json.loads(entity.action_config.input_mapping.value) if entity.action_config.input_mapping else None,
        "emit_event_type": entity.action_config.emit_event_type,
        "emit_event_payload": json.loads(entity.action_config.emit_event_payload.value) if entity.action_config.emit_event_payload else None,
    }
    model.execution_policy = {
        "max_concurrent": entity.execution_policy.max_concurrent,
        "timeout_seconds": entity.execution_policy.timeout_seconds,
        "retry_count": entity.execution_policy.retry_count,
        "retry_delay_seconds": entity.execution_policy.retry_delay_seconds,
    }
    model.enabled = entity.enabled.value
    model.updated_at = entity.updated_at.value
