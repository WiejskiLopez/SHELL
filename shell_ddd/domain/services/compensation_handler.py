"""CompensationHandler — Saga compensation hook invoked when a workflow aborts.

When ``Workflow.abort`` is called, the configured CompensationHandler runs
to release resources, undo side effects or notify external systems. The
default implementation is a no-op so the abort path stays clean for the PoC.

This is a *driving* contract from the domain perspective; concrete
implementations live in the infrastructure layer when real cleanup is needed.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.workflow import Workflow


class CompensationHandler(Protocol):
    """Synchronous compensation hook called from ``Workflow.abort``."""

    def compensate(self, workflow: Workflow, reason: str) -> None:
        """Run any cleanup/compensation needed for the aborted workflow."""
        ...


class NoOpCompensationHandler:
    """Default — performs no compensation."""

    def compensate(self, workflow: Workflow, reason: str) -> None:
        return None
