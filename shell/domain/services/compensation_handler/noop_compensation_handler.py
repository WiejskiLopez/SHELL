from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.entities.workflow import Workflow


class NoOpCompensationHandler:
    """Default — performs no compensation."""

    def compensate(self, workflow: Workflow, reason: str) -> None:
        return None
