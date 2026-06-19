from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.base.entity import Entity
from shell.domain.platform.value_objects.ids import GraphNodeDefinitionId

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.mode import Mode


class GraphNodeDefinition(Entity[GraphNodeDefinitionId]):
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
        "status_initial",
        "extra",
        "script",
        "script_type",
    )

    def __init__(
        self,
        id: GraphNodeDefinitionId,
        position: int,
        mode: Mode,
        role: str,
        node_type: str,
        model: str = "",
        command: str = "",
        timeout: int = 0,
        retries: int = 0,
        log_level: str = "INFO",
        max_step: int | None = None,
        no_ask_user: bool = False,
        autopilot: bool = False,
        status_initial: str = "",
        extra: dict[str, object] | None = None,
        script: str = "",
        script_type: str = "",
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
        self.status_initial = status_initial
        self.extra = extra or {}
        self.script = script
        self.script_type = script_type
