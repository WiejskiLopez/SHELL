"""Builders producing Scheduling BC ORM model instances for seeding and tests."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.scheduling_service.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (
    SchedulerExecutionModel,
)


def build_scheduler_definition_model(
    *,
    scheduler_definition_id: str,
    name: str,
    description: str | None,
    source_context: str,
    trigger_event_type: str,
    trigger_filter: dict[str, object] | None,
    action_type: str,
    action_config: dict[str, object],
    execution_policy: dict[str, object] | None,
    enabled: bool,
    created_at: datetime | None = None,
) -> SchedulerDefinitionModel:
    """Build a SchedulerDefinitionModel with deterministic values."""
    now = created_at or datetime.now(tz=UTC)
    return SchedulerDefinitionModel(
        id=scheduler_definition_id,
        name=name,
        description=description,
        source_context=source_context,
        trigger_event_type=trigger_event_type,
        trigger_filter=trigger_filter,
        action_type=action_type,
        action_config=action_config,
        execution_policy=execution_policy,
        enabled=enabled,
        created_at=now,
        changed_at=now,
    )


def build_scheduler_execution_model(
    *,
    scheduler_execution_id: str,
    scheduler_definition_id: str,
    status: str,
    trigger_event_id: str | None = None,
    trigger_event_type: str | None = None,
    action_ref: str | None = None,
    action_ref_type: str | None = None,
    input_state: dict[str, object] | None = None,
    output_state: dict[str, object] | None = None,
    error: str | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    created_at: datetime | None = None,
) -> SchedulerExecutionModel:
    """Build a SchedulerExecutionModel with deterministic values."""
    now = created_at or datetime.now(tz=UTC)
    return SchedulerExecutionModel(
        id=scheduler_execution_id,
        scheduler_definition_id=scheduler_definition_id,
        status=status,
        trigger_event_id=trigger_event_id,
        trigger_event_type=trigger_event_type,
        action_ref=action_ref,
        action_ref_type=action_ref_type,
        input_state=input_state,
        output_state=output_state,
        error=error,
        started_at=started_at,
        completed_at=completed_at,
        created_at=now,
        changed_at=now,
    )


__all__ = [
    "build_scheduler_definition_model",
    "build_scheduler_execution_model",
]
