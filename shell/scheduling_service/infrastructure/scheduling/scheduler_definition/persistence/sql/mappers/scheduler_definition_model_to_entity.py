from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.enabled import Enabled
from shell.platform.types import JsonStr
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
    SchedulerDefinition,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.action_config import (
    ActionConfig,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.execution_policy import (
    ExecutionPolicy,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_description import (
    SchedulerDescription,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_name import (
    SchedulerName,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.trigger_config import (
    TriggerConfig,
)

if TYPE_CHECKING:
    from shell.scheduling_service.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
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
    action_config_raw = model.action_config
    action_config = ActionConfig(
        action_type=model.action_type,
        graph_definition_id=cast("str | None", action_config_raw.get("graph_definition_id")),
        input_mapping=JsonStr(json.dumps(action_config_raw.get("input_mapping")))
        if action_config_raw.get("input_mapping")
        else None,
        emit_event_type=cast("str | None", action_config_raw.get("emit_event_type")),
        emit_event_payload=JsonStr(json.dumps(action_config_raw.get("emit_event_payload")))
        if action_config_raw.get("emit_event_payload")
        else None,
    )
    execution_policy_raw = model.execution_policy or {}
    policy = ExecutionPolicy(
        max_concurrent=cast("int", execution_policy_raw.get("max_concurrent", 1)),
        timeout_seconds=cast("int | None", execution_policy_raw.get("timeout_seconds")),
        retry_count=cast("int", execution_policy_raw.get("retry_count", 0)),
        retry_delay_seconds=cast("int", execution_policy_raw.get("retry_delay_seconds", 0)),
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
        changed_at=ChangedAt.from_datetime(model.changed_at),
    )
