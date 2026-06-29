from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
    GraphNodeDefinitionId,
)
from shell.domain.definition.value_objects.autopilot import Autopilot
from shell.domain.definition.value_objects.command_text import CommandText
from shell.domain.definition.value_objects.initial_status import InitialStatus
from shell.domain.definition.value_objects.log_level import LogLevel
from shell.domain.definition.value_objects.max_step import MaxStep
from shell.domain.definition.value_objects.model_name import ModelName
from shell.domain.definition.value_objects.no_ask_user import NoAskUser
from shell.domain.definition.value_objects.node_position import NodePosition
from shell.domain.definition.value_objects.node_role_name import NodeRoleName
from shell.domain.definition.value_objects.node_type_name import NodeTypeName
from shell.domain.definition.value_objects.retry_count import RetryCount
from shell.domain.definition.value_objects.script_text import ScriptText
from shell.domain.definition.value_objects.script_type_name import ScriptTypeName
from shell.domain.definition.value_objects.transition_timeout_seconds import TransitionTimeoutSeconds
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.platform.value_objects.mode import Mode


class GraphNodeDefinition(AggregateRoot[GraphNodeDefinitionId]):
    __slots__ = (
        "_graph_definition_id",
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
        graph_definition_id: GraphDefinitionId,
        position: NodePosition,
        mode: Mode,
        role: NodeRoleName,
        node_type: NodeTypeName,
        model: ModelName | None = None,
        command: CommandText | None = None,
        timeout: TransitionTimeoutSeconds | None = None,
        retries: RetryCount | None = None,
        log_level: LogLevel | None = None,
        max_step: MaxStep | None = None,
        no_ask_user: NoAskUser | None = None,
        autopilot: Autopilot | None = None,
        status_initial: InitialStatus | None = None,
        script: ScriptText | None = None,
        script_type: ScriptTypeName | None = None,
    ) -> None:
        super().__init__(id)
        self._graph_definition_id = graph_definition_id
        self._position = position if isinstance(position, NodePosition) else NodePosition(position)
        self._mode = mode
        self._role = role if isinstance(role, NodeRoleName) else NodeRoleName(role)
        self._node_type = node_type if isinstance(node_type, NodeTypeName) else NodeTypeName(node_type)
        self._model = model if model is None or isinstance(model, ModelName) else ModelName(model)
        self._command = command if command is None or isinstance(command, CommandText) else CommandText(command)
        self._timeout = timeout if timeout is None or isinstance(timeout, TransitionTimeoutSeconds) else TransitionTimeoutSeconds(timeout)
        self._retries = retries if retries is None or isinstance(retries, RetryCount) else RetryCount(retries)
        self._log_level = log_level if log_level is None or isinstance(log_level, LogLevel) else LogLevel(log_level)
        self._max_step = max_step if max_step is None or isinstance(max_step, MaxStep) else MaxStep(max_step)
        self._no_ask_user = no_ask_user if no_ask_user is None or isinstance(no_ask_user, NoAskUser) else NoAskUser(no_ask_user)
        self._autopilot = autopilot if autopilot is None or isinstance(autopilot, Autopilot) else Autopilot(autopilot)
        self._status_initial = status_initial if status_initial is None or isinstance(status_initial, InitialStatus) else InitialStatus(status_initial)
        self._script = script if script is None or isinstance(script, ScriptText) else ScriptText(script)
        self._script_type = script_type if script_type is None or isinstance(script_type, ScriptTypeName) else ScriptTypeName(script_type)

    @classmethod
    def restore(
        cls,
        id: GraphNodeDefinitionId,
        graph_definition_id: GraphDefinitionId,
        position: NodePosition,
        mode: Mode,
        role: NodeRoleName,
        node_type: NodeTypeName,
        model: ModelName | None = None,
        command: CommandText | None = None,
        timeout: TransitionTimeoutSeconds | None = None,
        retries: RetryCount | None = None,
        log_level: LogLevel | None = None,
        max_step: MaxStep | None = None,
        no_ask_user: NoAskUser | None = None,
        autopilot: Autopilot | None = None,
        status_initial: InitialStatus | None = None,
        script: ScriptText | None = None,
        script_type: ScriptTypeName | None = None,
    ) -> GraphNodeDefinition:
        return cls(
            id=id,
            graph_definition_id=graph_definition_id,
            position=position,
            mode=mode,
            role=role,
            node_type=node_type,
            model=model,
            command=command,
            timeout=timeout,
            retries=retries,
            log_level=log_level,
            max_step=max_step,
            no_ask_user=no_ask_user,
            autopilot=autopilot,
            status_initial=status_initial,
            script=script,
            script_type=script_type,
        )

    @classmethod
    def create(
        cls,
        id: GraphNodeDefinitionId,
        graph_definition_id: GraphDefinitionId,
        position: NodePosition,
        mode: Mode,
        role: NodeRoleName,
        node_type: NodeTypeName,
        model: ModelName | None = None,
        command: CommandText | None = None,
        timeout: TransitionTimeoutSeconds | None = None,
        retries: RetryCount | None = None,
        log_level: LogLevel | None = None,
        max_step: MaxStep | None = None,
        no_ask_user: NoAskUser | None = None,
        autopilot: Autopilot | None = None,
        status_initial: InitialStatus | None = None,
        script: ScriptText | None = None,
        script_type: ScriptTypeName | None = None,
        now: datetime | None = None,
    ) -> GraphNodeDefinition:
        instance = cls(
            id=id,
            graph_definition_id=graph_definition_id,
            position=position,
            mode=mode,
            role=role,
            node_type=node_type,
            model=model,
            command=command,
            timeout=timeout,
            retries=retries,
            log_level=log_level,
            max_step=max_step,
            no_ask_user=no_ask_user,
            autopilot=autopilot,
            status_initial=status_initial,
            script=script,
            script_type=script_type,
        )

        from shell.domain.definition.aggregates.graph_node_definition.events.graph_node_definition_created_event import (
            GraphNodeDefinitionCreatedEvent,
        )

        if now is not None:
            instance.append_event(
                GraphNodeDefinitionCreatedEvent.now(
                    graph_node_definition_id=id,
                    graph_definition_id=graph_definition_id,
                    position=position,
                    role=role,
                    node_type=node_type,
                    now=CreatedAt.from_datetime(now),
                )
            )

        return instance

    @property
    def graph_definition_id(self) -> GraphDefinitionId:
        return self._graph_definition_id

    @property
    def position(self) -> NodePosition:
        return self._position

    @property
    def mode(self) -> Mode:
        return self._mode

    @property
    def role(self) -> NodeRoleName:
        return self._role

    @property
    def node_type(self) -> NodeTypeName:
        return self._node_type

    @property
    def model(self) -> ModelName | None:
        return self._model

    @property
    def command(self) -> CommandText | None:
        return self._command

    @property
    def timeout(self) -> TransitionTimeoutSeconds | None:
        return self._timeout

    @property
    def retries(self) -> RetryCount | None:
        return self._retries

    @property
    def log_level(self) -> LogLevel | None:
        return self._log_level

    @property
    def max_step(self) -> MaxStep | None:
        return self._max_step

    @property
    def no_ask_user(self) -> NoAskUser | None:
        return self._no_ask_user

    @property
    def autopilot(self) -> Autopilot | None:
        return self._autopilot

    @property
    def status_initial(self) -> InitialStatus | None:
        return self._status_initial

    @property
    def script(self) -> ScriptText | None:
        return self._script

    @property
    def script_type(self) -> ScriptTypeName | None:
        return self._script_type
