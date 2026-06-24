from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.value_objects.ids import GraphNodeDefinitionId
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.mode import Mode


class GraphNodeDefinition(Entity[GraphNodeDefinitionId]):
    __slots__ = (
        "_position",
        "_mode",
        "_role",
        "_node_type",
        "_model",
        "_command",
        "_timeout",
        "_retries",
        "_log_level",
        "_max_step",
        "_no_ask_user",
        "_autopilot",
        "_status_initial",
        "_script",
        "_script_type",
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
        script: str = "",
        script_type: str = "",
    ) -> None:
        super().__init__(id)
        self._position = position
        self._mode = mode
        self._role = role
        self._node_type = node_type
        self._model = model
        self._command = command
        self._timeout = timeout
        self._retries = retries
        self._log_level = log_level
        self._max_step = max_step
        self._no_ask_user = no_ask_user
        self._autopilot = autopilot
        self._status_initial = status_initial
        self._script = script
        self._script_type = script_type

    @property
    def position(self) -> int:
        return self._position

    @property
    def mode(self) -> Mode:
        return self._mode

    @property
    def role(self) -> str:
        return self._role

    @property
    def node_type(self) -> str:
        return self._node_type

    @property
    def model(self) -> str:
        return self._model

    @property
    def command(self) -> str:
        return self._command

    @property
    def timeout(self) -> int:
        return self._timeout

    @property
    def retries(self) -> int:
        return self._retries

    @property
    def log_level(self) -> str:
        return self._log_level

    @property
    def max_step(self) -> int | None:
        return self._max_step

    @property
    def no_ask_user(self) -> bool:
        return self._no_ask_user

    @property
    def autopilot(self) -> bool:
        return self._autopilot

    @property
    def status_initial(self) -> str:
        return self._status_initial

    @property
    def script(self) -> str:
        return self._script

    @property
    def script_type(self) -> str:
        return self._script_type
