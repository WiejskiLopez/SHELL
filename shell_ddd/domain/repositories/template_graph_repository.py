from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.template_graph import TemplateGraph
    from shell_ddd.domain.value_objects.ids import TemplateGraphId


class TemplateGraphRepository(Protocol):
    async def get(self, graph_id: TemplateGraphId) -> TemplateGraph | None: ...
    async def get_template_graph_by_name(self, template_graph_by_name: str) -> TemplateGraph | None: ...
    async def save(self, graph: TemplateGraph) -> None: ...
