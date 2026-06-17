from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.entities.template_graph import TemplateGraph
    from shell.domain.entities.template_graph_node import TemplateGraphNode
    from shell.domain.value_objects.ids import TemplateGraphId, TemplateGraphNodeId


class TemplateGraphRepository(Protocol):
    async def get(self, graph_id: TemplateGraphId) -> TemplateGraph | None: ...

    async def get_template_graph_by_name(
        self, template_graph_by_name: str
    ) -> TemplateGraph | None: ...

    async def save(self, graph: TemplateGraph) -> None: ...


class TemplateGraphNodeRepository(Protocol):
    async def get_by_id(self, node_id: TemplateGraphNodeId) -> TemplateGraphNode | None: ...

    async def save(self, node: TemplateGraphNode) -> None: ...
