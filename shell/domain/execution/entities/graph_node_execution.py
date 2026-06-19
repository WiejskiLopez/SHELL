"""Task aggregate root with embedded Graph and GraphNodes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.base.entity import Entity
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.mode import Mode


class GraphNodeExecution(Entity[GraphNodeExecutionId]):
    """A single node definition within a Task's graph."""

    __slots__ = (
        "position",
        "mode",
        "role",
        "node_type",
        "model",
        "command",
        "timeout",
        "retries",
        "log_level",
        "max_step",
        "no_ask_user",
        "autopilot",
        "task_execution_id",
        "source_dir",
        "status_initial",
        "extra",
    )

    def __init__(
        self,
        id: GraphNodeExecutionId,
        position: int,
        mode: Mode,
        role: str,
        node_type: str,
        model: str = "",
        command: str = "",
        timeout: int = 0,
        retries: int = 0,
        log_level: str = "INFO",
        max_step: int = 0,
        no_ask_user: bool = False,
        autopilot: bool = False,
        task_execution_id: str = "",
        source_dir: str = "",
        status_initial: str = "",
        extra: dict[str, object] | None = None,
    ) -> None:
        super().__init__(id)
        self.position = position
        self.mode = mode
        self.role = role
        self.node_type = node_type
        self.model = model
        self.command = command
        self.timeout = timeout
        self.retries = retries
        self.log_level = log_level
        self.max_step = max_step
        self.no_ask_user = no_ask_user
        self.autopilot = autopilot
        self.task_execution_id = task_execution_id
        self.source_dir = source_dir
        self.status_initial = status_initial
        self.extra = extra or {}
