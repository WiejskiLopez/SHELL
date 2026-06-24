from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_transition_execution.value_objects.graph_node_transition_execution_id import (
    GraphNodeTransitionExecutionId,
)
from shell.domain.execution.value_objects.edge_type import EdgeType
from shell.domain.execution.value_objects.transition_status import TransitionStatus
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_transition_execution.value_objects.spawn_spec import (
        SpawnSpec,
    )
    from shell.domain.execution.value_objects.node_role import NodeRole


class GraphNodeTransitionExecution(AggregateRoot[GraphNodeTransitionExecutionId]):
    __slots__ = (
        "_graph_execution_id",
        "_source_node_execution_id",
        "_target_node_execution_id",
        "_spawn_spec",
        "_edge_type",
        "_condition_expression",
        "_max_iterations",
        "_status",
        "_current_iteration",
    )

    _graph_execution_id: GraphExecutionId
    _source_node_execution_id: GraphNodeExecutionId
    _target_node_execution_id: GraphNodeExecutionId | None
    _spawn_spec: SpawnSpec | None
    _edge_type: EdgeType
    _condition_expression: str | None
    _max_iterations: int | None
    _status: TransitionStatus
    _current_iteration: int

    def __init__(
        self,
        id_: GraphNodeTransitionExecutionId,
        graph_execution_id: GraphExecutionId,
        source_node_execution_id: GraphNodeExecutionId,
        edge_type: EdgeType,
        target_node_execution_id: GraphNodeExecutionId | None = None,
        spawn_spec: SpawnSpec | None = None,
        condition_expression: str | None = None,
        max_iterations: int | None = None,
    ) -> None:
        super().__init__(id_)
        self._graph_execution_id = graph_execution_id
        self._source_node_execution_id = source_node_execution_id
        self._target_node_execution_id = target_node_execution_id
        self._spawn_spec = spawn_spec
        self._edge_type = edge_type
        self._condition_expression = condition_expression
        self._max_iterations = max_iterations
        self._status = TransitionStatus.EVALUATED
        self._current_iteration = 0

    @classmethod
    def create_sequence(
        cls,
        id_: GraphNodeTransitionExecutionId,
        graph_execution_id: GraphExecutionId,
        source_node_execution_id: GraphNodeExecutionId,
        target_node_execution_id: GraphNodeExecutionId,
    ) -> GraphNodeTransitionExecution:
        return cls(
            id_=id_,
            graph_execution_id=graph_execution_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
            edge_type=EdgeType.SEQUENCE,
        )

    @classmethod
    def create_conditional(
        cls,
        id_: GraphNodeTransitionExecutionId,
        graph_execution_id: GraphExecutionId,
        source_node_execution_id: GraphNodeExecutionId,
        target_node_execution_id: GraphNodeExecutionId,
        condition_expression: str,
    ) -> GraphNodeTransitionExecution:
        return cls(
            id_=id_,
            graph_execution_id=graph_execution_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
            edge_type=EdgeType.CONDITIONAL,
            condition_expression=condition_expression,
        )

    @classmethod
    def create_loop(
        cls,
        id_: GraphNodeTransitionExecutionId,
        graph_execution_id: GraphExecutionId,
        source_node_execution_id: GraphNodeExecutionId,
        target_node_execution_id: GraphNodeExecutionId,
        max_iterations: int,
    ) -> GraphNodeTransitionExecution:
        return cls(
            id_=id_,
            graph_execution_id=graph_execution_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
            edge_type=EdgeType.LOOP,
            max_iterations=max_iterations,
        )

    @classmethod
    def create_spawn_subgraph(
        cls,
        id_: GraphNodeTransitionExecutionId,
        graph_execution_id: GraphExecutionId,
        source_node_execution_id: GraphNodeExecutionId,
        spawn_spec: SpawnSpec,
    ) -> GraphNodeTransitionExecution:
        return cls(
            id_=id_,
            graph_execution_id=graph_execution_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=None,
            edge_type=EdgeType.SPAWN_SUBGRAPH,
            spawn_spec=spawn_spec,
        )

    @classmethod
    def create_error_handler(
        cls,
        id_: GraphNodeTransitionExecutionId,
        graph_execution_id: GraphExecutionId,
        source_node_execution_id: GraphNodeExecutionId,
        target_node_execution_id: GraphNodeExecutionId,
    ) -> GraphNodeTransitionExecution:
        return cls(
            id_=id_,
            graph_execution_id=graph_execution_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
            edge_type=EdgeType.ERROR_HANDLER,
        )

    @classmethod
    def create_timeout(
        cls,
        id_: GraphNodeTransitionExecutionId,
        graph_execution_id: GraphExecutionId,
        source_node_execution_id: GraphNodeExecutionId,
        target_node_execution_id: GraphNodeExecutionId,
    ) -> GraphNodeTransitionExecution:
        return cls(
            id_=id_,
            graph_execution_id=graph_execution_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
            edge_type=EdgeType.TIMEOUT,
        )

    @classmethod
    def create_default(
        cls,
        id_: GraphNodeTransitionExecutionId,
        graph_execution_id: GraphExecutionId,
        source_node_execution_id: GraphNodeExecutionId,
        target_node_execution_id: GraphNodeExecutionId,
    ) -> GraphNodeTransitionExecution:
        return cls(
            id_=id_,
            graph_execution_id=graph_execution_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
            edge_type=EdgeType.DEFAULT,
        )

    def take(self, now: datetime) -> None:
        if self._status != TransitionStatus.EVALUATED:
            raise InvalidTransitionError(
                f"Cannot take transition in status {self._status}"
            )
        self._status = TransitionStatus.TAKEN
        from shell.domain.execution.aggregates.graph_node_transition_execution.events.transition_taken_event import (
            TransitionTakenEvent,
        )

        self.append_event(
            TransitionTakenEvent.now(
                transition_id=self._id,
                source_node_id=self._source_node_execution_id,
                target_node_id=self._target_node_execution_id,
                now=now,
            )
        )

    def skip(self) -> None:
        if self._status != TransitionStatus.EVALUATED:
            raise InvalidTransitionError(
                f"Cannot skip transition in status {self._status}"
            )
        self._status = TransitionStatus.SKIPPED

    def loop(self, now: datetime) -> None:
        if self._status != TransitionStatus.TAKEN:
            raise InvalidTransitionError(
                f"Cannot loop transition in status {self._status}"
            )
        if self._edge_type != EdgeType.LOOP:
            raise InvalidTransitionError(
                f"Cannot loop non-LOOP transition (type={self._edge_type})"
            )
        self._current_iteration += 1
        self._status = TransitionStatus.EVALUATED
        from shell.domain.execution.aggregates.graph_node_transition_execution.events.transition_looped_event import (
            TransitionLoopedEvent,
        )

        self.append_event(
            TransitionLoopedEvent.now(
                transition_id=self._id,
                source_node_id=self._source_node_execution_id,
                now=now,
                iteration=self._current_iteration,
            )
        )

    def evaluate_condition(self, condition_result: bool, now: datetime) -> None:
        if self._edge_type != EdgeType.CONDITIONAL:
            raise InvalidTransitionError(
                f"Cannot evaluate condition for non-CONDITIONAL transition (type={self._edge_type})"
            )
        if self._status != TransitionStatus.EVALUATED:
            raise InvalidTransitionError(
                f"Cannot evaluate condition in status {self._status}"
            )
        from shell.domain.execution.aggregates.graph_node_transition_execution.events.transition_condition_evaluated_event import (
            TransitionConditionEvaluatedEvent,
        )

        self.append_event(
            TransitionConditionEvaluatedEvent.now(
                transition_id=self._id,
                source_node_id=self._source_node_execution_id,
                now=now,
                condition_result=condition_result,
            )
        )
        if condition_result and self._target_node_execution_id is not None:
            self.take(now)
        else:
            self.skip()

    def handle_error(
        self, failed_node_id: GraphNodeExecutionId, handler_node_id: GraphNodeExecutionId, now: datetime
    ) -> None:
        if self._edge_type != EdgeType.ERROR_HANDLER:
            raise InvalidTransitionError(
                f"Cannot handle error for non-ERROR_HANDLER transition (type={self._edge_type})"
            )
        from shell.domain.execution.aggregates.graph_node_transition_execution.events.transition_error_handled_event import (
            TransitionErrorHandledEvent,
        )

        self.append_event(
            TransitionErrorHandledEvent.now(
                transition_id=self._id,
                failed_node_id=failed_node_id,
                handler_node_id=handler_node_id,
                now=now,
            )
        )
        self._status = TransitionStatus.TAKEN

    def handle_timeout(
        self, node_id: GraphNodeExecutionId, handler_node_id: GraphNodeExecutionId, now: datetime
    ) -> None:
        if self._edge_type != EdgeType.TIMEOUT:
            raise InvalidTransitionError(
                f"Cannot handle timeout for non-TIMEOUT transition (type={self._edge_type})"
            )
        from shell.domain.execution.aggregates.graph_node_transition_execution.events.transition_timed_out_event import (
            TransitionTimedOutEvent,
        )

        self.append_event(
            TransitionTimedOutEvent.now(
                transition_id=self._id,
                node_id=node_id,
                handler_node_id=handler_node_id,
                now=now,
            )
        )
        self._status = TransitionStatus.TAKEN

    @property
    def graph_execution_id(self) -> GraphExecutionId:
        return self._graph_execution_id

    @property
    def source_node_execution_id(self) -> GraphNodeExecutionId:
        return self._source_node_execution_id

    @property
    def target_node_execution_id(self) -> GraphNodeExecutionId | None:
        return self._target_node_execution_id

    @property
    def spawn_spec(self) -> SpawnSpec | None:
        return self._spawn_spec

    @property
    def edge_type(self) -> EdgeType:
        return self._edge_type

    @property
    def condition_expression(self) -> str | None:
        return self._condition_expression

    @property
    def max_iterations(self) -> int | None:
        return self._max_iterations

    @property
    def status(self) -> TransitionStatus:
        return self._status

    @property
    def current_iteration(self) -> int:
        return self._current_iteration


class InvalidTransitionError(Exception):
    pass
