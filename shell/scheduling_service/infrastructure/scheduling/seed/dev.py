"""Development seed data for the Scheduling bounded context.

Idempotent: records are inserted only when missing, so the seed can be
run repeatedly against the same database without creating duplicates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from shell.scheduling_service.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (
    SchedulerExecutionModel,
)
from shell.scheduling_service.infrastructure.scheduling.seed.builders import (
    build_scheduler_definition_model,
    build_scheduler_execution_model,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEV_ID_PREFIX = "dev"

_DEFINITIONS_DATA: list[dict[str, Any]] = [
    {
        "scheduler_definition_id": f"{DEV_ID_PREFIX}-scheduler-outbox-relay",
        "name": "outbox-relay",
        "description": "Processes pending outbox events and publishes them to inbox",
        "source_context": "platform",
        "trigger_event_type": "OutboxPollingEvent",
        "trigger_filter": {"event_types": ["*"]},
        "action_type": "relay",
        "action_config": {"batch_size": 100, "max_retries": 3, "target": "outbox_to_inbox"},
        "execution_policy": {
            "max_concurrent": 1,
            "timeout_seconds": 60,
            "retry_policy": {"max_attempts": 3, "backoff_seconds": 5},
        },
        "enabled": True,
    },
    {
        "scheduler_definition_id": f"{DEV_ID_PREFIX}-scheduler-cleanup",
        "name": "cleanup-stale",
        "description": "Cleans up stale executions and state records",
        "source_context": "execution",
        "trigger_event_type": "CleanupEvent",
        "trigger_filter": {"age_hours": 72},
        "action_type": "cleanup",
        "action_config": {"batch_size": 500, "retention_hours": 168},
        "execution_policy": {"max_concurrent": 1, "timeout_seconds": 300},
        "enabled": True,
    },
    {
        "scheduler_definition_id": f"{DEV_ID_PREFIX}-scheduler-health",
        "name": "health-check",
        "description": "Periodic health check for all active sessions",
        "source_context": "session",
        "trigger_event_type": "HealthCheckEvent",
        "trigger_filter": {},
        "action_type": "monitor",
        "action_config": {"check_interval": 60, "timeout_threshold": 300},
        "execution_policy": {"max_concurrent": 5, "timeout_seconds": 30},
        "enabled": True,
    },
]


def seed_dev_sync(session: Session) -> None:
    """Insert dev scheduler definitions and executions when missing."""
    for definition_data in _DEFINITIONS_DATA:
        definition_id = str(definition_data["scheduler_definition_id"])
        existing_definition = session.execute(
            select(SchedulerDefinitionModel).where(SchedulerDefinitionModel.id == definition_id)
        ).scalar_one_or_none()

        if existing_definition is None:
            session.add(build_scheduler_definition_model(**definition_data))

        execution_id = f"{definition_id}-exec"
        existing_execution = session.execute(
            select(SchedulerExecutionModel).where(SchedulerExecutionModel.id == execution_id)
        ).scalar_one_or_none()
        if existing_execution is not None:
            continue

        session.add(
            build_scheduler_execution_model(
                scheduler_execution_id=execution_id,
                scheduler_definition_id=definition_id,
                status="idle",
                input_state={"source_context": definition_data["source_context"]},
                action_ref=str(definition_data["action_type"]),
                action_ref_type="action_type",
            )
        )


__all__ = ["DEV_ID_PREFIX", "seed_dev_sync"]
