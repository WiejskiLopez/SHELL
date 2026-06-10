"""Task aggregate root with embedded Graph and GraphNodes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.entities.graph import Graph
from shell_ddd.domain.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import TaskId, TemplateGraphId
    from shell_ddd.domain.value_objects.task_name import TaskName


@dataclass(slots=True)
class Task:
    """Task aggregate root."""

    id: TaskId
    name: TaskName
    version: int
    hash: Hash
    body_md: str
    template_graph_id: TemplateGraphId
    is_current: bool
    created_at: datetime
    graph: Graph | None = None

    @classmethod
    def new(
            cls,
            *,
            id_: TaskId,
            name: TaskName,
            body_md: str,
            template_graph_id: TemplateGraphId,
            now: datetime,
    ) -> Task:
        content_hash = Hash.of(body_md)
        return cls(
            id=id_,
            name=name,
            version=1,
            hash=content_hash,
            body_md=body_md,
            template_graph_id=template_graph_id,
            is_current=True,
            created_at=now,
        )
