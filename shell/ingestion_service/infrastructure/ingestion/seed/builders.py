"""Builders producing Ingestion BC delivery model instances for seeding and tests.

The audit/outbox/inbox models are built dynamically by the platform factory,
so each builder takes the concrete model class as its first argument.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_audit_event_model(
    model: type[Any],
    *,
    event_id: str,
    integration_event_name: str,
    payload: dict[str, object],
    occurred_at: datetime | None = None,
) -> Any:
    """Build an audit event row with deterministic values."""
    return model(
        id=event_id,
        integration_event_name=integration_event_name,
        payload=payload,
        occurred_at=occurred_at or datetime.now(tz=UTC),
    )


def build_outbox_event_model(
    model: type[Any],
    *,
    id: str,
    event_id: str,
    source_service: str,
    integration_event_name: str,
    payload: dict[str, object],
    aggregate_id: str,
    correlation_id: str,
    causation_id: str,
    schema_version: int = 1,
    published_at: datetime | None = None,
    occurred_at: datetime | None = None,
) -> Any:
    """Build an outbox event row with deterministic values."""
    return model(
        id=id,
        event_id=event_id,
        source_service=source_service,
        integration_event_name=integration_event_name,
        payload=payload,
        occurred_at=occurred_at or datetime.now(tz=UTC),
        aggregate_id=aggregate_id,
        schema_version=schema_version,
        correlation_id=correlation_id,
        causation_id=causation_id,
        published_at=published_at,
    )


def build_inbox_event_model(
    model: type[Any],
    *,
    id: str,
    outbox_id: str,
    event_id: str,
    source_service: str,
    integration_event_name: str,
    payload: dict[str, object],
    aggregate_id: str,
    correlation_id: str,
    causation_id: str,
    occurred_at: datetime | None = None,
    received_at: datetime | None = None,
    processed_at: datetime | None = None,
    status: str = "PENDING",
) -> Any:
    """Build an inbox event row with deterministic values."""
    return model(
        id=id,
        outbox_id=outbox_id,
        event_id=event_id,
        source_service=source_service,
        integration_event_name=integration_event_name,
        payload=payload,
        occurred_at=occurred_at or datetime.now(tz=UTC),
        aggregate_id=aggregate_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
        received_at=received_at or datetime.now(tz=UTC),
        processed_at=processed_at,
        status=status,
    )


__all__ = [
    "build_audit_event_model",
    "build_inbox_event_model",
    "build_outbox_event_model",
]
