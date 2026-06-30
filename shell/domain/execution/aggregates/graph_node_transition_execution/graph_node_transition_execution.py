from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.graph_node_transition_execution.value_objects.graph_node_transition_execution_id import (
    GraphNodeTransitionExecutionId,
)
from shell.domain.execution.value_objects.condition_result import ConditionResult
from shell.domain.execution.value_objects.current_iteration import CurrentIteration
from shell.domain.execution.value_objects.edge_type import EdgeType
from shell.domain.execution.value_objects.max_iterations import MaxIterations
from shell.domain.execution.value_objects.transition_status import TransitionStatus
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

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
    from shell.domain.execution.value_objects.condition_language import ConditionLanguage
    from shell.domain.platform.value_objects.condition_expression import ConditionExpression


class GraphNodeTransitionExecution(AggregateRoot[GraphNodeTransitionExecutionId]):
    __slots__ = (
        "_graph_execution_id",
        "_source_node_execution_id",
        "_target_node_execution_id",
        "_spawn_spec",
        "_edge_type",
        "_condition_expression",
        "_condition_language",
        "_max_iterations",
        "_status",
        "_current_iteration",
    )

    _graph_execution_id: GraphExecutionId
    _source_node_execution_id: GraphNodeExecutionId
    _target_node_execution_id: GraphNodeExecutionId | None
    _spawn_spec: SpawnSpec | None
    _edge_type: EdgeType
    _condition_expression: ConditionExpression | None
    _condition_language: ConditionLanguage | None
    _max_iterations: MaxIterations
    _status: TransitionStatus
    _current_iteration: CurrentIteration

    def __init__(
        self,
        id_: GraphNodeTransitionExecutionId,
        graph_execution_id: GraphExecutionId,
        source_node_execution_id: GraphNodeExecutionId,
        edge_type: EdgeType,
        target_node_execution_id: GraphNodeExecutionId | None = None,
        spawn_spec: SpawnSpec | None = None,
        condition_expression: ConditionExpression | None = None,
        condition_language: ConditionLanguage | None = None,
        max_iterations: MaxIterations | None = None,
        status: TransitionStatus | None = None,
        current_iteration: CurrentIteration | None = None,
    ) -> None:
        super().__init__(id_)
        self._graph_execution_id = graph_execution_id
        self._source_node_execution_id = source_node_execution_id
        self._target_node_execution_id = target_node_execution_id
        self._spawn_spec = spawn_spec
        self._edge_type = edge_type
        self._condition_expression = condition_expression
        self._condition_language = condition_language
        self._max_iterations = max_iterations if max_iterations is not None else MaxIterations(None)
        self._status = status if status is not None else TransitionStatus.EVALUATED
        self._current_iteration = (
            current_iteration if current_iteration is not None else CurrentIteration(0)
        )

    @classmethod
    def restore(
        cls,
        id_: GraphNodeTransitionExecutionId,
        graph_execution_id: GraphExecutionId,
        source_node_execution_id: GraphNodeExecutionId,
        edge_type: EdgeType,
        target_node_execution_id: GraphNodeExecutionId | None = None,
        spawn_spec: SpawnSpec | None = None,
        condition_expression: ConditionExpression | None = None,
        condition_language: ConditionLanguage | None = None,
        max_iterations: MaxIterations | None = None,
        status: TransitionStatus | None = None,
        current_iteration: CurrentIteration | None = None,
    ) -> Self:
        return cls(
            id_=id_,
            graph_execution_id=graph_execution_id,
            source_node_execution_id=source_node_execution_id,
            edge_type=edge_type,
            target_node_execution_id=target_node_execution_id,
            spawn_spec=spawn_spec,
            condition_expression=condition_expression,
            condition_language=condition_language,
            max_iterations=max_iterations,
            status=status,
            current_iteration=current_iteration,
        )

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
        condition_expression: ConditionExpression,
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
        max_iterations: MaxIterations,
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
            raise InvalidTransitionError(f"Cannot take transition in status {self._status}")
        self._status = TransitionStatus.TAKEN
        from shell.domain.execution.aggregates.graph_node_transition_execution.events.graph_node_transition_execution_transition_applied_event import (
            GraphNodeTransitionExecutionTransitionAppliedEvent,
        )

        if self._target_node_execution_id is None:
            raise InvalidTransitionError("Cannot take transition without target node")
        self.append_event(
            GraphNodeTransitionExecutionTransitionAppliedEvent.now(
                transition_id=self._id,
                source_node_id=self._source_node_execution_id,
                target_node_id=self._target_node_execution_id,
                now=CreatedAt.from_datetime(now),
            )
        )

    def skip(self) -> None:
        if self._status != TransitionStatus.EVALUATED:
            raise InvalidTransitionError(f"Cannot skip transition in status {self._status}")
        self._status = TransitionStatus.SKIPPED

    def loop(self, now: datetime) -> None:
        if self._status != TransitionStatus.TAKEN:
            raise InvalidTransitionError(f"Cannot loop transition in status {self._status}")
        if self._edge_type != EdgeType.LOOP:
            raise InvalidTransitionError(
                f"Cannot loop non-LOOP transition (type={self._edge_type})"
            )
        self._current_iteration = CurrentIteration(self._current_iteration.value + 1)
        self._status = TransitionStatus.EVALUATED
        from shell.domain.execution.aggregates.graph_node_transition_execution.events.graph_node_transition_execution_looped_event import (
            GraphNodeTransitionExecutionLoopedEvent,
        )

        self.append_event(
            GraphNodeTransitionExecutionLoopedEvent.now(
                transition_id=self._id,
                source_node_id=self._source_node_execution_id,
                now=CreatedAt.from_datetime(now),
                iteration=self._current_iteration,
            )
        )

    def evaluate_condition(self, condition_result: bool, now: datetime) -> None:
        if self._edge_type != EdgeType.CONDITIONAL:
            raise InvalidTransitionError(
                f"Cannot evaluate condition for non-CONDITIONAL transition (type={self._edge_type})"
            )
        if self._status != TransitionStatus.EVALUATED:
            raise InvalidTransitionError(f"Cannot evaluate condition in status {self._status}")
        from shell.domain.execution.aggregates.graph_node_transition_execution.events.graph_node_transition_execution_condition_evaluated_event import (
            GraphNodeTransitionExecutionConditionEvaluatedEvent,
        )

        self.append_event(
            GraphNodeTransitionExecutionConditionEvaluatedEvent.now(
                transition_id=self._id,
                source_node_id=self._source_node_execution_id,
                now=CreatedAt.from_datetime(now),
                condition_result=ConditionResult(condition_result),
            )
        )
        if condition_result and self._target_node_execution_id is not None:
            self.take(now)
        else:
            self.skip()

    def handle_error(
        self,
        failed_node_id: GraphNodeExecutionId,
        handler_node_id: GraphNodeExecutionId,
        now: datetime,
    ) -> None:
        if self._edge_type != EdgeType.ERROR_HANDLER:
            raise InvalidTransitionError(
                f"Cannot handle error for non-ERROR_HANDLER transition (type={self._edge_type})"
            )
        from shell.domain.execution.aggregates.graph_node_transition_execution.events.graph_node_transition_execution_error_handled_event import (
            GraphNodeTransitionExecutionErrorHandledEvent,
        )

        self.append_event(
            GraphNodeTransitionExecutionErrorHandledEvent.now(
                transition_id=self._id,
                failed_node_id=failed_node_id,
                handler_node_id=handler_node_id,
                now=CreatedAt.from_datetime(now),
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
        from shell.domain.execution.aggregates.graph_node_transition_execution.events.graph_node_transition_execution_timeout_expired_event import (
            GraphNodeTransitionExecutionTimeoutExpiredEvent,
        )

        self.append_event(
            GraphNodeTransitionExecutionTimeoutExpiredEvent.now(
                transition_id=self._id,
                node_id=node_id,
                handler_node_id=handler_node_id,
                now=CreatedAt.from_datetime(now),
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
    def condition_expression(self) -> ConditionExpression | None:
        return self._condition_expression

    @property
    def condition_language(self) -> ConditionLanguage | None:
        return self._condition_language

    @property
    def max_iterations(self) -> MaxIterations:
        return self._max_iterations

    @property
    def status(self) -> TransitionStatus:
        return self._status

    @property
    def current_iteration(self) -> CurrentIteration:
        return self._current_iteration


class InvalidTransitionError(Exception):
    pass
