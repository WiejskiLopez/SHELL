from __future__ import annotations

import json
from typing import TYPE_CHECKING

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
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.enabled import Enabled
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
        SchedulerDefinitionModel,
    )


def scheduler_definition_model_to_entity(
    model: SchedulerDefinitionModel,
) -> SchedulerDefinition:
    trigger_config = TriggerConfig(
        source_context=model.source_context,
        trigger_event_type=model.trigger_event_type,
        trigger_filter=JsonStr(json.dumps(dict(model.trigger_filter)))
        if model.trigger_filter
        else None,
    )
    action_config = ActionConfig(
        action_type=model.action_type,
        graph_definition_id=model.action_config.get("graph_definition_id"),
        input_mapping=JsonStr(json.dumps(model.action_config.get("input_mapping")))
        if model.action_config.get("input_mapping")
        else None,
        emit_event_type=model.action_config.get("emit_event_type"),
        emit_event_payload=JsonStr(json.dumps(model.action_config.get("emit_event_payload")))
        if model.action_config.get("emit_event_payload")
        else None,
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
        updated_at=UpdatedAt.from_datetime(model.updated_at),
    )
