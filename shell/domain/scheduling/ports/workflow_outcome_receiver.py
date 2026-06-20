from __future__ import annotations

from typing import Protocol


class WorkflowOutcomeReceiver(Protocol):
    async def on_workflow_completed(self, workflow_id: str) -> None: ...

    async def on_workflow_failed(self, workflow_id: str, error: str) -> None: ...
