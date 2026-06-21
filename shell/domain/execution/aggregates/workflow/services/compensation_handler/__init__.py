"""CompensationHandler — Saga compensation hook invoked when a workflow aborts."""

from __future__ import annotations

from shell.domain.execution.aggregates.workflow.services.compensation_handler.compensation_handler import (
    CompensationHandler,
)
from shell.domain.execution.aggregates.workflow.services.compensation_handler.noop_compensation_handler import (
    NoOpCompensationHandler,
)

__all__ = [
    "CompensationHandler",
    "NoOpCompensationHandler",
]
