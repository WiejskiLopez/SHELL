from __future__ import annotations

from typing import Protocol


class GraphExecutionLauncher(Protocol):
    async def launch(
        self,
        *,
        graph_definition_id: str,
        input_state: dict,
        correlation_id: str,
    ) -> str:  # returns graph_execution_id
        ...
