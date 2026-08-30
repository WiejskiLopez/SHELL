from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.scheduling_service.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)

if TYPE_CHECKING:
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
        SchedulerDefinition,
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
        trigger_filter=json.loads(entity.trigger_config.trigger_filter.value)
        if entity.trigger_config.trigger_filter
        else None,
        action_type=entity.action_config.action_type.value,
        action_config={
            "graph_definition_id": entity.action_config.graph_definition_id,
            "input_mapping": json.loads(entity.action_config.input_mapping.value)
            if entity.action_config.input_mapping
            else None,
            "emit_event_type": entity.action_config.emit_event_type,
            "emit_event_payload": json.loads(entity.action_config.emit_event_payload.value)
            if entity.action_config.emit_event_payload
            else None,
        },
        execution_policy={
            "max_concurrent": entity.execution_policy.max_concurrent,
            "timeout_seconds": entity.execution_policy.timeout_seconds,
            "retry_count": entity.execution_policy.retry_count,
            "retry_delay_seconds": entity.execution_policy.retry_delay_seconds,
        },
        enabled=entity.enabled.value,
        created_at=entity.created_at.value,
        changed_at=entity.changed_at.value,
    )
