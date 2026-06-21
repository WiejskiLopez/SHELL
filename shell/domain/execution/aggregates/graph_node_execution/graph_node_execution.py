"""GraphNodeExecution AggregateRoot — owns its payloads and emits PlannerResultEvent."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.graph_execution_id import (
    GraphExecutionId,  # noqa: TC002 — GraphExecutionId używany w konstruktorze i typach propertisów GraphNodeExecution
)
from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_input import (
    GraphNodeExecutionStateInput,  # noqa: TC002 — GraphNodeExecutionStateInput używany w konstruktorze i typach propertisów GraphNodeExecution
)
from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_output import (
    GraphNodeExecutionStateOutput,  # noqa: TC002 — GraphNodeExecutionStateOutput używany w konstruktorze i typach propertisów GraphNodeExecution
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.platform.base import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.mode import Mode


class GraphNodeExecution(AggregateRoot[GraphNodeExecutionId]):
    """A single node in a graph execution — owns its input/output payloads."""

    __slots__ = (
        "_graph_execution_id",
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
        "timeout_seconds",
        "max_retries",
        "retry_delay_seconds",
        "_input_states",
        "_output_states",
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
        timeout_seconds: int = 0,
        max_retries: int = 0,
        retry_delay_seconds: int = 0,
        graph_execution_id: GraphExecutionId | None = None,
        input_states: list[GraphNodeExecutionStateInput] | None = None,
        output_states: list[GraphNodeExecutionStateOutput] | None = None,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
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
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self._input_states = list(input_states) if input_states else []
        self._output_states = list(output_states) if output_states else []

    @property
    def graph_execution_id(self) -> GraphExecutionId | None:
        return self._graph_execution_id

    @property
    def input_states(self) -> tuple[GraphNodeExecutionStateInput, ...]:
        return tuple(self._input_states)

    @property
    def output_states(self) -> tuple[GraphNodeExecutionStateOutput, ...]:
        return tuple(self._output_states)

    def add_input_state(self, payload: GraphNodeExecutionStateInput) -> None:
        self._input_states.append(payload)

    def add_output_state(self, payload: GraphNodeExecutionStateOutput) -> None:
        self._output_states.append(payload)

    def get_latest_input_state(self) -> GraphNodeExecutionStateInput | None:
        current = [p for p in self._input_states if p.is_current]
        return current[0] if current else None

    def get_latest_output_state(self) -> GraphNodeExecutionStateOutput | None:
        current = [p for p in self._output_states if p.is_current]
        return current[0] if current else None

    def record_planner_result(
        self,
        *,
        stdout: str,
        graph_execution_id: GraphExecutionId,
        now: object = None,
    ) -> None:
        from datetime import datetime as dt

        try:
            plan = json.loads(stdout)
        except (json.JSONDecodeError, ValueError):
            return

        stage = plan.get("stage", "")
        spawn = tuple(plan.get("spawn", []))

        if not stage and not spawn:
            return

        from shell.domain.execution.aggregates.graph_node_execution.events.planner_result_event import (
            PlannerResultEvent,
        )

        self.append_event(
            PlannerResultEvent.now(
                graph_node_execution_id=self.id,
                graph_execution_id=graph_execution_id,
                stage=stage,
                spawn=spawn,
                raw_json=stdout,
                now=now or dt.now(),
            )
        )
