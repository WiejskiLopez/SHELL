"""GraphNodeExecution AggregateRoot — owns its payloads and emits PlannerResultEvent."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from shell.domain.platform.base import AggregateRoot
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
)

from shell.domain.execution.entities.graph_node_execution_input_payload import (
    GraphNodeExecutionInputPayload,
)
from shell.domain.execution.entities.graph_node_execution_output_payload import (
    GraphNodeExecutionOutputPayload,
)

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.platform.events import DomainEvent
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
        "sub_graph_definition_id",
        "sub_graph_definition_version",
        "timeout_seconds",
        "max_retries",
        "retry_delay_seconds",
        "extra",
        "_input_payloads",
        "_output_payloads",
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
        graph_execution_id: GraphExecutionId | None = None,
        input_payloads: list[GraphNodeExecutionInputPayload] | None = None,
        output_payloads: list[GraphNodeExecutionOutputPayload] | None = None,
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
        self.sub_graph_definition_id = sub_graph_definition_id
        self.sub_graph_definition_version = sub_graph_definition_version
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.extra = extra or {}
        self._input_payloads = list(input_payloads) if input_payloads else []
        self._output_payloads = list(output_payloads) if output_payloads else []

    @property
    def graph_execution_id(self) -> GraphExecutionId | None:
        return self._graph_execution_id

    @property
    def input_payloads(self) -> tuple[GraphNodeExecutionInputPayload, ...]:
        return tuple(self._input_payloads)

    @property
    def output_payloads(self) -> tuple[GraphNodeExecutionOutputPayload, ...]:
        return tuple(self._output_payloads)

    def add_input_payload(self, payload: GraphNodeExecutionInputPayload) -> None:
        self._input_payloads.append(payload)

    def add_output_payload(self, payload: GraphNodeExecutionOutputPayload) -> None:
        self._output_payloads.append(payload)

    def get_latest_input_payload(self) -> GraphNodeExecutionInputPayload | None:
        current = [p for p in self._input_payloads if p.is_current]
        return current[0] if current else None

    def get_latest_output_payload(self) -> GraphNodeExecutionOutputPayload | None:
        current = [p for p in self._output_payloads if p.is_current]
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

        from shell.domain.execution.events.planner_result_event import (
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
