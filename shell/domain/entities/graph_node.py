"""Task aggregate root with embedded Graph and GraphNodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.value_objects.ids import NodeId
    from shell.domain.value_objects.mode import Mode


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
    task_execution_id: str = ""
    source_dir: str = ""
    work_dir: str = ""
    status_initial: str = ""
    extra: dict[str, object] = field(default_factory=dict)
