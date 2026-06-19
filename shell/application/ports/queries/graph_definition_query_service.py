from __future__ import annotations

from typing import Protocol

from shell.application.dto import GraphDefinitionDto


class GraphDefinitionQueryService(Protocol):
    """Port do pobierania historii sesji/czatu."""

    async def get_graph_definition_by_name(self, name: str) -> GraphDefinitionDto | None: ...
