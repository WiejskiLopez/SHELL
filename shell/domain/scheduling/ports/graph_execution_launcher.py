from __future__ import annotations

from typing import Any, Protocol


class GraphExecutionLauncher(Protocol):
    async def launch(
        self,
        *,
        graph_definition_id: str,
        input_state: dict[str, Any],
    ) -> str:  # returns graph_execution_id
        ...
