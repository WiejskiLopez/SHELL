from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from shell.platform.domain.types import JsonStr

if TYPE_CHECKING:
    from shell.application.definition.graph_definition.dto.graph_definition import (
        GraphDefinitionDto,
    )


class GraphDefinitionQueryService(Protocol):
    async def get_by_id(self, definition_id: str) -> GraphDefinitionDto | None: ...

    async def get_graph_definition_by_semantic(
        self,
        semantic_query: JsonStr,
    ) -> GraphDefinitionDto | None: ...
