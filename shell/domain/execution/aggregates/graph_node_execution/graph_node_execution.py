from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.value_objects.graph_node_execution_status import (
    GraphNodeExecutionStatus,
)
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.error_description import ErrorDescription
from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_input import (
    GraphNodeExecutionStateInput,
)
from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_output import (
    GraphNodeExecutionStateOutput,
)
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )


class GraphNodeExecution(AggregateRoot[GraphNodeExecutionId]):
    __slots__ = (
        # V3 fields
        "_graph_execution_id",
        "_order",
        "_status",
        "_state_inputs",
        "_state_outputs",
        # Legacy (deprecated)
        "_role",
        "_position",
        "_mode",
        "_node_type",
        "_model",
        "_command",
        "_retries",
        "_log_level",
        "_max_step",
        "_no_ask_user",
        "_autopilot",
        "_task_execution_id",
        "_source_dir",
        "_status_initial",
        "_timeout_seconds",
        "_max_retries",
        "_retry_delay_seconds",
    )

    def __init__(
        self,
        id: GraphNodeExecutionId,
        graph_execution_id: GraphExecutionId | None = None,
        role: NodeRole = NodeRole.PLANNER,
        order: NodeOrder | None = None,
        position: int = 0,
        mode: Any = None,
        node_type: str = "",
        model: str = "",
        command: str = "",
        timeout: int | None = None,  # deprecated — use _legacy_timeout
        _legacy_timeout: int = 0,
        retries: int = 0,
        log_level: str = "INFO",
        max_step: int = 0,
        no_ask_user: bool = False,
        autopilot: bool = False,
        task_execution_id: str = "",
        source_dir: str = "",
        status_initial: str = "",
        timeout_seconds: int = 0,
        max_retries: int = 0,
        retry_delay_seconds: int = 0,
        input_states: list[GraphNodeExecutionStateInput] | None = None,
        output_states: list[GraphNodeExecutionStateOutput] | None = None,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
        self._order = order or NodeOrder(0)
        self._role = role
        self._status = GraphNodeExecutionStatus.PENDING
        self._state_inputs = list(input_states) if input_states else []
        self._state_outputs = list(output_states) if output_states else []

        # Legacy fields
        self._position = position
        self._mode = mode
        self._node_type = node_type
        self._model = model
        self._command = command
        self._retries = retries
        self._log_level = log_level
        self._max_step = max_step
        self._no_ask_user = no_ask_user
        self._autopilot = autopilot
        self._task_execution_id = task_execution_id
        self._source_dir = source_dir
        self._status_initial = status_initial
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds

    # --- Factory ---

    @classmethod
    def new(
        cls,
        *,
        id: GraphNodeExecutionId,
        graph_execution_id: GraphExecutionId | None = None,
        parent_graph_execution_id: GraphExecutionId | None = None,
        role: NodeRole = NodeRole.PLANNER,
        order: NodeOrder | None = None,
        position: int = 0,
        mode: Any = None,
        node_type: str = "",
        model: str = "",
        command: str = "",
        timeout: int | None = None,
        retries: int = 0,
        log_level: str = "INFO",
        max_step: int = 0,
        no_ask_user: bool = False,
        autopilot: bool = False,
        task_execution_id: str = "",
        source_dir: str = "",
        status_initial: str = "",
        timeout_seconds: int = 0,
        max_retries: int = 0,
        retry_delay_seconds: int = 0,
        now: datetime,
    ) -> GraphNodeExecution:
        instance = cls(
            id=id,
            graph_execution_id=graph_execution_id,
            role=role,
            order=order,
            position=position,
            mode=mode,
            node_type=node_type,
            model=model,
            command=command,
            timeout=timeout,
            retries=retries,
            log_level=log_level,
            max_step=max_step,
            no_ask_user=no_ask_user,
            autopilot=autopilot,
            task_execution_id=task_execution_id,
            source_dir=source_dir,
            status_initial=status_initial,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
        )
        if parent_graph_execution_id is not None and graph_execution_id is not None:
            from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_initialized_event import (
                GraphNodeExecutionInitializedEvent,
            )

            instance.append_event(
                GraphNodeExecutionInitializedEvent.now(
                    node_id=id,
                    graph_execution_id=graph_execution_id,
                    parent_graph_execution_id=parent_graph_execution_id,
                    now=now,
                )
            )
        return instance

    # --- V3 FSM ---

    def start(self, now: datetime) -> None:
        if self._status != GraphNodeExecutionStatus.PENDING:
            raise InvalidNodeStateError(
                f"Cannot start node in status {self._status}"
            )
        self._status = GraphNodeExecutionStatus.RUNNING
        from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_started_event import (
            GraphNodeExecutionStartedEvent,
        )

        self.append_event(
            GraphNodeExecutionStartedEvent.now(
                node_id=self._id,
                role=self._role,
                now=now,
            )
        )

    def complete(self, result: dict[str, Any] | None, now: datetime) -> None:
        if self._status != GraphNodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(
                f"Cannot complete node in status {self._status}"
            )
        self._status = GraphNodeExecutionStatus.COMPLETED
        if result:
            self._append_output(result, now)
        from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_completed_event import (
            GraphNodeExecutionCompletedEvent,
        )

        self.append_event(
            GraphNodeExecutionCompletedEvent.now(
                node_id=self._id,
                role=self._role,
                now=now,
                result=result,
            )
        )

    def fail(self, error: ErrorDescription | str, now: datetime) -> None:
        if self._status != GraphNodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(
                f"Cannot fail node in status {self._status}"
            )
        self._status = GraphNodeExecutionStatus.FAILED
        from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_failed_event import (
            GraphNodeExecutionFailedEvent,
        )

        if isinstance(error, str):
            error = ErrorDescription(error)

        self.append_event(
            GraphNodeExecutionFailedEvent.now(
                node_id=self._id,
                role=self._role,
                now=now,
                error=error,
            )
        )

    def timeout(self, now: datetime) -> None:
        if self._status != GraphNodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(
                f"Cannot timeout node in status {self._status}"
            )
        self._status = GraphNodeExecutionStatus.TIMED_OUT
        from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_timed_out_event import (
            GraphNodeExecutionTimedOutEvent,
        )

        self.append_event(
            GraphNodeExecutionTimedOutEvent.now(
                node_id=self._id,
                role=self._role,
                now=now,
            )
        )

    # --- State I/O ---

    def add_output_state(self, state: GraphNodeExecutionStateOutput) -> None:
        self._state_outputs.append(state)

    def add_input_state(self, payload: dict[str, Any], now: datetime) -> None:
        from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_input import (
            GraphNodeExecutionStateInput,
        )
        from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_state_input_id import (
            GraphNodeExecutionStateInputId,
        )

        state = GraphNodeExecutionStateInput(
            id=GraphNodeExecutionStateInputId.generate(),
            graph_node_execution_id=self._id,
            payload=payload,
            created_at=now,
        )
        self._state_inputs.append(state)

    def _append_output(self, payload: dict[str, Any], now: datetime) -> None:
        from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_output import (
            GraphNodeExecutionStateOutput,
        )
        from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_state_output_id import (
            GraphNodeExecutionStateOutputId,
        )

        state = GraphNodeExecutionStateOutput(
            id=GraphNodeExecutionStateOutputId.generate(),
            graph_node_execution_id=self._id,
            payload=payload,
            created_at=now,
        )
        self._state_outputs.append(state)

    # --- Properties ---

    @property
    def graph_execution_id(self) -> GraphExecutionId | None:
        return self._graph_execution_id

    def get_latest_input_state(self) -> GraphNodeExecutionStateInput | None:
        if not self._state_inputs:
            return None
        return self._state_inputs[-1]

    def get_latest_output_state(self) -> GraphNodeExecutionStateOutput | None:
        if not self._state_outputs:
            return None
        return self._state_outputs[-1]

    @property
    def role(self) -> NodeRole:
        return self._role

    @property
    def order(self) -> NodeOrder:
        return self._order

    @property
    def status(self) -> GraphNodeExecutionStatus:
        return self._status

    @property
    def state_inputs(self) -> tuple:
        return tuple(self._state_inputs)

    @property
    def state_outputs(self) -> tuple:
        return tuple(self._state_outputs)

    @property
    def input_states(self) -> tuple:
        return tuple(self._state_inputs)

    @property
    def output_states(self) -> tuple:
        return tuple(self._state_outputs)

    # --- Legacy properties (deprecated) ---

    @property
    def position(self) -> int:
        return self._position

    @property
    def mode(self) -> Any:
        return self._mode

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
    def retries(self) -> int:
        return self._retries

    @property
    def log_level(self) -> str:
        return self._log_level

    @property
    def max_step(self) -> int:
        return self._max_step

    @property
    def no_ask_user(self) -> bool:
        return self._no_ask_user

    @property
    def autopilot(self) -> bool:
        return self._autopilot

    @property
    def task_execution_id(self) -> str:
        return self._task_execution_id

    @property
    def source_dir(self) -> str:
        return self._source_dir

    @property
    def status_initial(self) -> str:
        return self._status_initial

    @property
    def timeout_seconds(self) -> int:
        return self._timeout_seconds

    @property
    def max_retries(self) -> int:
        return self._max_retries

    @property
    def retry_delay_seconds(self) -> int:
        return self._retry_delay_seconds


class InvalidNodeStateError(Exception):
    pass
