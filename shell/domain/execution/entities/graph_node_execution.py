"""Task aggregate root with embedded Graph and GraphNodes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
        "sub_graph_definition_id",
        "sub_graph_definition_version",
        "timeout_seconds",
        "max_retries",
        "retry_delay_seconds",
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
        sub_graph_definition_id: str | None = None,
        sub_graph_definition_version: int | None = None,
        timeout_seconds: int = 0,
        max_retries: int = 0,
        retry_delay_seconds: int = 0,
        extra: dict[str, Any] | None = None,
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
        self.sub_graph_definition_id = sub_graph_definition_id
        self.sub_graph_definition_version = sub_graph_definition_version
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.extra = extra or {}
