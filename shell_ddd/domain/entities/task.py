"""Task aggregate root with embedded Graph and GraphNodes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import GraphId, NodeId, TaskId
    from shell_ddd.domain.value_objects.mode import Mode
    from shell_ddd.domain.value_objects.task_name import TaskName


@dataclass(slots=True)
class GraphNode:
    """A single node definition within a Task's graph."""

    id: NodeId
    position: int
    node_dir: str
    mode: Mode
    role: str
    node_type: str
    model: str = ""
    command: str = ""
    timeout: int = 0
    retries: int = 0
    log_level: str = "INFO"
    max_step: int = 0
    no_ask_user: bool = False
    autopilot: bool = False
    task_name: str = ""
    source_dir: str = ""
    work_dir: str = ""
    status_initial: str = ""
    extra: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class Graph:
    """Graph embedded in a Task aggregate."""

    id: GraphId
    task_id: TaskId
    raw_dict: dict[str, object]
    nodes: list[GraphNode] = field(default_factory=list)


@dataclass(slots=True)
class Task:
    """Task aggregate root."""

    id: TaskId
    name: TaskName
    version: int
    hash: Hash
    body_md: str
    body_yaml_raw: str
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
        body_yaml_raw: str,
        now: datetime | None = None,
    ) -> Task:
        created = now or datetime.now(tz=UTC)
        content_hash = Hash.of(body_md + body_yaml_raw)
        return cls(
            id=id_,
            name=name,
            version=1,
            hash=content_hash,
            body_md=body_md,
            body_yaml_raw=body_yaml_raw,
            is_current=True,
            created_at=created,
        )
