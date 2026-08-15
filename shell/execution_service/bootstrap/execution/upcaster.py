"""Execution contract payload migrations."""

from __future__ import annotations

from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster

_TASK_EXECUTION_CREATED = "TaskExecutionCreatedIntegrationEvent"


def _task_execution_created_v1_to_v2(payload: dict[str, object]) -> dict[str, object]:
    normalized = dict(payload)
    if "task_execution_id" not in normalized and "id" in normalized:
        normalized["task_execution_id"] = normalized.pop("id")
    return normalized


def build_execution_upcaster() -> PayloadUpcaster:
    """Build the explicitly versioned execution payload migrations."""
    return PayloadUpcaster(
        {
            _TASK_EXECUTION_CREATED: {1: _task_execution_created_v1_to_v2},
        }
    )
