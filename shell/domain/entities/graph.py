"""Graph aggregate root.

A Graph is the concrete realisation of a workflow plan for a specific Task.
It is built from a TemplateGraph in reaction to the ``TaskCreated`` event
(see ``BuildGraphOnTaskCreated`` event handler) — a Task does not know
which Graph realises it; the Graph holds the back-reference (``task_id``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from shell.domain.entities.base import AggregateRoot
from shell.domain.entities.graph_node import GraphNode
from shell.domain.events.events import GraphBuilt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.entities.template_graph import TemplateGraph
    from shell.domain.value_objects.ids import (
        GraphId,
        NodeId,
        TaskId,
        TemplateGraphId,
    )


class _NodeIdFactory(Protocol):
    """Structural type for a callable that produces a fresh NodeId."""

    def __call__(self) -> NodeId: ...


class Graph(AggregateRoot["GraphId"]):
    """Graph aggregate root — owns its GraphNodes."""

    __slots__ = (
        "_task_id",
        "_template_graph_id",
        "_raw_dict",
        "_nodes",
    )

    _task_id: TaskId
    _template_graph_id: TemplateGraphId
    _raw_dict: dict[str, object]
    _nodes: list[GraphNode]

    def __init__(
        self,
        id: GraphId,
        task_id: TaskId,
        template_graph_id: TemplateGraphId,
        raw_dict: dict[str, object] | None = None,
        nodes: list[GraphNode] | None = None,
    ) -> None:
        super().__init__(id)
        self._task_id = task_id
        self._template_graph_id = template_graph_id
        self._raw_dict = dict(raw_dict) if raw_dict else {}
        self._nodes = list(nodes) if nodes else []

    @property
    def task_id(self) -> TaskId:
        return self._task_id

    @property
    def template_graph_id(self) -> TemplateGraphId:
        return self._template_graph_id

    @property
    def raw_dict(self) -> dict[str, object]:
        return self._raw_dict

    @property
    def nodes(self) -> list[GraphNode]:
        return self._nodes

    @classmethod
    def from_template(
        cls,
        *,
        id_: GraphId,
        task_id: TaskId,
        template: TemplateGraph,
        node_id_factory: _NodeIdFactory,
        now: datetime,
    ) -> Graph:
        """Build a Graph from a TemplateGraph snapshot. Emits GraphBuilt."""
        from shell.domain.value_objects.mode import Mode

        nodes: list[GraphNode] = []
        for tn in template.nodes:
            mode = tn.mode if isinstance(tn.mode, Mode) else Mode(str(tn.mode))
            nodes.append(
                GraphNode(
                    id=node_id_factory(),
                    position=tn.position,
                    node_dir="",
                    mode=mode,
                    role=tn.role,
                    node_type=tn.node_type,
                    model=tn.model,
                    command=tn.command,
                    timeout=tn.timeout,
                    retries=tn.retries,
                    log_level=tn.log_level,
                    max_step=tn.max_step or 0,
                    no_ask_user=tn.no_ask_user,
                    autopilot=tn.autopilot,
                    task_id="",
                    source_dir="",
                    work_dir="",
                    status_initial=tn.status_initial,
                    extra=dict(tn.extra),
                )
            )
        graph = cls(
            id=id_,
            task_id=task_id,
            template_graph_id=template.id,
            raw_dict={},
            nodes=nodes,
        )
        graph.append_event(
            GraphBuilt.now(
                graph_id=id_,
                task_id=task_id,
                template_graph_id=template.id,
                now=now,
            )
        )
        return graph

    def add_node(self, node: GraphNode) -> None:
        self._nodes.append(node)
