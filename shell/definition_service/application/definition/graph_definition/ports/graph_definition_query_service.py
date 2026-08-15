from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.definition_service.application.definition.graph_definition.dto.graph_definition import (
        GraphDefinitionDto,
    )
    from shell.platform.types import JsonStr


class GraphDefinitionQueryService(Protocol):
    async def get_by_id(self, definition_id: str) -> GraphDefinitionDto | None: ...

    async def get_graph_definition_by_semantic(
        self,
        semantic_query: JsonStr,
    ) -> GraphDefinitionDto | None: ...
