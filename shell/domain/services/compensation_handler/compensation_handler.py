from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.aggregates.workflow import Workflow


class CompensationHandler(Protocol):
    """Synchronous compensation hook called from ``Workflow.abort``."""

    def compensate(self, workflow: Workflow, reason: str) -> None:
        ...
