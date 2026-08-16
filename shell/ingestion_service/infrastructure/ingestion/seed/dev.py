"""Development seed data for the Ingestion bounded context.

Idempotent: records are inserted only when missing, so the seed can be
run repeatedly against the same database without creating duplicates.

This BC owns the platform delivery demonstration data (audit, outbox and
inbox event streams) bound to the Ingestion BC registry. Demo outbox rows
are marked as already published and demo inbox rows as already processed,
so delivery workers never re-publish or re-claim them at runtime.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
    InboxEventModel,
    OutboxEventModel,
)
from shell.ingestion_service.infrastructure.ingestion.seed.builders import (
    build_audit_event_model,
    build_inbox_event_model,
    build_outbox_event_model,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.persistence.sql.seed_helpers import seed_if_missing

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEV_ID_PREFIX = "dev"
_NOW = datetime.now(tz=UTC)

_AUDIT_MODEL: type[Any] = PERSISTENCE_DELIVERY_MODELS.audit
_OUTBOX_MODEL: type[Any] = OutboxEventModel
_INBOX_MODEL: type[Any] = InboxEventModel

_AUDIT_EVENTS_DATA: list[dict[str, Any]] = [
    {
        "event_id": f"{DEV_ID_PREFIX}-audit-1",
        "event_type": "user.login",
        "payload": {"user_id": f"{DEV_ID_PREFIX}-user-alice", "ip": "192.168.1.10"},
    },
    {
        "event_id": f"{DEV_ID_PREFIX}-audit-2",
        "event_type": "workflow.created",
        "payload": {
            "workflow_id": f"{DEV_ID_PREFIX}-workflow-simple",
            "session_id": f"{DEV_ID_PREFIX}-session-alice-1",
        },
    },
    {
        "event_id": f"{DEV_ID_PREFIX}-audit-3",
        "event_type": "task.completed",
        "payload": {"task_id": f"{DEV_ID_PREFIX}-task-simple-1", "status": "completed"},
    },
    {
        "event_id": f"{DEV_ID_PREFIX}-audit-4",
        "event_type": "scheduler.triggered",
        "payload": {
            "scheduler_id": f"{DEV_ID_PREFIX}-scheduler-outbox-relay",
            "action": "relay",
        },
    },
    {
        "event_id": f"{DEV_ID_PREFIX}-audit-5",
        "event_type": "project.archived",
        "payload": {"project_id": f"{DEV_ID_PREFIX}-project-gamma", "reason": "completed"},
    },
]

_OUTBOX_EVENTS_DATA: list[dict[str, Any]] = [
    {
        "event_id": f"{DEV_ID_PREFIX}-outbox-1",
        "event_type": "workflow.completed",
        "payload": {"workflow_id": f"{DEV_ID_PREFIX}-workflow-simple"},
        "correlation_id": "corr-outbox-1",
        "causation_id": "cause-outbox-1",
        "published_at": _NOW,
    },
    {
        "event_id": f"{DEV_ID_PREFIX}-outbox-2",
        "event_type": "task.created",
        "payload": {"task_id": f"{DEV_ID_PREFIX}-task-planner-2"},
        "correlation_id": "corr-outbox-2",
        "causation_id": "cause-outbox-2",
        "published_at": _NOW,
    },
    {
        "event_id": f"{DEV_ID_PREFIX}-outbox-3",
        "event_type": "workflow.started",
        "payload": {"workflow_id": f"{DEV_ID_PREFIX}-workflow-pipeline"},
        "correlation_id": "corr-outbox-3",
        "causation_id": "cause-outbox-3",
        "published_at": _NOW,
    },
]

_INBOX_EVENTS_DATA: list[dict[str, Any]] = [
    {
        "event_id": f"{DEV_ID_PREFIX}-inbox-1",
        "event_type": "workflow.completed",
        "payload": {"workflow_id": f"{DEV_ID_PREFIX}-workflow-simple"},
        "correlation_id": "corr-inbox-1",
        "causation_id": "cause-inbox-1",
        "status": InboxStatus.PROCESSED.value,
        "processed_at": _NOW,
    },
    {
        "event_id": f"{DEV_ID_PREFIX}-inbox-2",
        "event_type": "task.created",
        "payload": {"task_id": f"{DEV_ID_PREFIX}-task-planner-2"},
        "correlation_id": "corr-inbox-2",
        "causation_id": "cause-inbox-2",
        "status": InboxStatus.PROCESSED.value,
        "processed_at": _NOW,
    },
    {
        "event_id": f"{DEV_ID_PREFIX}-inbox-3",
        "event_type": "scheduler.ready",
        "payload": {"scheduler_id": f"{DEV_ID_PREFIX}-scheduler-health"},
        "correlation_id": "corr-inbox-3",
        "causation_id": "cause-inbox-3",
        "status": InboxStatus.PROCESSED.value,
        "processed_at": _NOW,
    },
]


def seed_dev_sync(session: Session) -> None:
    """Insert dev audit, outbox and inbox events when missing."""
    for event_data in _AUDIT_EVENTS_DATA:
        seed_if_missing(
            session,
            _AUDIT_MODEL,
            str(event_data["event_id"]),
            lambda event_data=event_data: build_audit_event_model(_AUDIT_MODEL, **event_data),
        )

    for event_data in _OUTBOX_EVENTS_DATA:
        seed_if_missing(
            session,
            _OUTBOX_MODEL,
            str(event_data["event_id"]),
            lambda event_data=event_data: build_outbox_event_model(_OUTBOX_MODEL, **event_data),
        )

    for event_data in _INBOX_EVENTS_DATA:
        seed_if_missing(
            session,
            _INBOX_MODEL,
            str(event_data["event_id"]),
            lambda event_data=event_data: build_inbox_event_model(_INBOX_MODEL, **event_data),
        )


__all__ = ["DEV_ID_PREFIX", "seed_dev_sync"]
