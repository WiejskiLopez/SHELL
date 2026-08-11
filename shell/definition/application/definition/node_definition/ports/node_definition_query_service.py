from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.definition.application.definition.node_definition.dto.node_definition import (
        NodeDefinitionDto,
    )


class NodeDefinitionQueryService(Protocol):
    async def get_by_id(self, node_definition_id: str) -> NodeDefinitionDto | None: ...
