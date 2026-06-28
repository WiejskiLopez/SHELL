from __future__ import annotations

from typing import Protocol

from shell.application.platform.dto import (
    GraphDefinitionDto,  # noqa: TC002 — GraphDefinitionDto używany jako typ zwracany w sygnaturach Protocol
)


class GraphDefinitionQueryService(Protocol):
    async def get_graph_definition(self, definition_id: str) -> GraphDefinitionDto | None: ...

    async def get_graph_definition_by_semantic_name(
        self, payload: dict[str, object],
    ) -> GraphDefinitionDto | None: ...


