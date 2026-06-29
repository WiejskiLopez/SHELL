from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_node_transition_definition.value_objects.graph_node_transition_definition_id import (
    GraphNodeTransitionDefinitionId,
)
from shell.domain.definition.value_objects.condition_language import ConditionLanguage
from shell.domain.definition.value_objects.data_mapping import DataMapping
from shell.domain.definition.value_objects.max_loop_count import MaxLoopCount
from shell.domain.definition.value_objects.retry_count import RetryCount
from shell.domain.definition.value_objects.transition_label import TransitionLabel
from shell.domain.definition.value_objects.transition_priority import TransitionPriority
from shell.domain.definition.value_objects.transition_retry_delay import TransitionRetryDelay
from shell.domain.definition.value_objects.transition_timeout_seconds import TransitionTimeoutSeconds
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.condition_expression import ConditionExpression
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.edge_type import EdgeType

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )


class GraphNodeTransitionDefinition(AggregateRoot[GraphNodeTransitionDefinitionId]):
    __slots__ = (
        "_graph_definition_id",
        "_source_node_definition_id",
        "_target_node_definition_id",
        "_transition_type",
        "_priority",
        "_condition_expression",
        "_condition_language",
        "_max_loop_count",
        "_timeout_seconds",
        "_retry_count",
        "_retry_delay_seconds",
        "_data_mapping",
        "_label",
    )

    def __init__(
        self,
        id: GraphNodeTransitionDefinitionId,
        graph_definition_id: GraphDefinitionId,
        source_node_definition_id: GraphNodeDefinitionId | None,
        target_node_definition_id: GraphNodeDefinitionId,
        transition_type: EdgeType,
        priority: TransitionPriority | None = None,
        condition_expression: ConditionExpression | None = None,
        condition_language: ConditionLanguage | None = None,
        max_loop_count: MaxLoopCount | None = None,
        timeout_seconds: TransitionTimeoutSeconds | None = None,
        retry_count: RetryCount | None = None,
        retry_delay_seconds: TransitionRetryDelay | None = None,
        data_mapping: DataMapping | None = None,
        label: TransitionLabel | None = None,
    ) -> None:
        if transition_type == EdgeType.CONDITIONAL and (condition_expression is None or (isinstance(condition_expression, ConditionExpression) and not condition_expression.value)):
            raise ValueError("CONDITIONAL transition requires condition_expression")
        super().__init__(id)
        self._graph_definition_id = graph_definition_id
        self._source_node_definition_id = source_node_definition_id
        self._target_node_definition_id = target_node_definition_id
        self._transition_type = transition_type
        self._priority = priority if priority is None or isinstance(priority, TransitionPriority) else TransitionPriority(priority)
        self._condition_expression = condition_expression if condition_expression is None or isinstance(condition_expression, ConditionExpression) else ConditionExpression(condition_expression)
        self._condition_language = condition_language if condition_language is None or isinstance(condition_language, ConditionLanguage) else ConditionLanguage(condition_language)
        self._max_loop_count = max_loop_count if max_loop_count is None or isinstance(max_loop_count, MaxLoopCount) else MaxLoopCount(max_loop_count)
        self._timeout_seconds = timeout_seconds if timeout_seconds is None or isinstance(timeout_seconds, TransitionTimeoutSeconds) else TransitionTimeoutSeconds(timeout_seconds)
        self._retry_count = retry_count if retry_count is None or isinstance(retry_count, RetryCount) else RetryCount(retry_count)
        self._retry_delay_seconds = retry_delay_seconds if retry_delay_seconds is None or isinstance(retry_delay_seconds, TransitionRetryDelay) else TransitionRetryDelay(retry_delay_seconds)
        self._data_mapping = data_mapping if data_mapping is None or isinstance(data_mapping, DataMapping) else DataMapping(data_mapping)
        self._label = label if label is None or isinstance(label, TransitionLabel) else TransitionLabel(label)

    @classmethod
    def restore(
        cls,
        id: GraphNodeTransitionDefinitionId,
        graph_definition_id: GraphDefinitionId,
        source_node_definition_id: GraphNodeDefinitionId | None,
        target_node_definition_id: GraphNodeDefinitionId,
        transition_type: EdgeType,
        priority: TransitionPriority | None = None,
        condition_expression: ConditionExpression | None = None,
        condition_language: ConditionLanguage | None = None,
        max_loop_count: MaxLoopCount | None = None,
        timeout_seconds: TransitionTimeoutSeconds | None = None,
        retry_count: RetryCount | None = None,
        retry_delay_seconds: TransitionRetryDelay | None = None,
        data_mapping: DataMapping | None = None,
        label: TransitionLabel | None = None,
    ) -> GraphNodeTransitionDefinition:
        return cls(
            id=id,
            graph_definition_id=graph_definition_id,
            source_node_definition_id=source_node_definition_id,
            target_node_definition_id=target_node_definition_id,
            transition_type=transition_type,
            priority=priority,
            condition_expression=condition_expression,
            condition_language=condition_language,
            max_loop_count=max_loop_count,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
            retry_delay_seconds=retry_delay_seconds,
            data_mapping=data_mapping,
            label=label,
        )

    @classmethod
    def create(
        cls,
        id: GraphNodeTransitionDefinitionId,
        graph_definition_id: GraphDefinitionId,
        source_node_definition_id: GraphNodeDefinitionId | None,
        target_node_definition_id: GraphNodeDefinitionId,
        transition_type: EdgeType,
        priority: TransitionPriority | None = None,
        condition_expression: ConditionExpression | None = None,
        condition_language: ConditionLanguage | None = None,
        max_loop_count: MaxLoopCount | None = None,
        timeout_seconds: TransitionTimeoutSeconds | None = None,
        retry_count: RetryCount | None = None,
        retry_delay_seconds: TransitionRetryDelay | None = None,
        data_mapping: DataMapping | None = None,
        label: TransitionLabel | None = None,
        now: datetime | None = None,
    ) -> GraphNodeTransitionDefinition:
        instance = cls(
            id=id,
            graph_definition_id=graph_definition_id,
            source_node_definition_id=source_node_definition_id,
            target_node_definition_id=target_node_definition_id,
            transition_type=transition_type,
            priority=priority,
            condition_expression=condition_expression,
            condition_language=condition_language,
            max_loop_count=max_loop_count,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
            retry_delay_seconds=retry_delay_seconds,
            data_mapping=data_mapping,
            label=label,
        )

        from shell.domain.definition.aggregates.graph_node_transition_definition.events.graph_node_transition_definition_created_event import (
            GraphNodeTransitionDefinitionCreatedEvent,
        )

        if now is not None:
            instance.append_event(
                GraphNodeTransitionDefinitionCreatedEvent.now(
                    graph_node_transition_definition_id=id,
                    graph_definition_id=graph_definition_id,
                    source_node_definition_id=source_node_definition_id,
                    target_node_definition_id=target_node_definition_id,
                    transition_type=transition_type,
                    now=CreatedAt.from_datetime(now),
                )
            )

        return instance

    @property
    def graph_definition_id(self) -> GraphDefinitionId:
        return self._graph_definition_id

    @property
    def source_node_definition_id(self) -> GraphNodeDefinitionId | None:
        return self._source_node_definition_id

    @property
    def target_node_definition_id(self) -> GraphNodeDefinitionId:
        return self._target_node_definition_id

    @property
    def transition_type(self) -> EdgeType:
        return self._transition_type

    @property
    def priority(self) -> TransitionPriority | None:
        return self._priority

    @property
    def condition_expression(self) -> ConditionExpression | None:
        return self._condition_expression

    @property
    def condition_language(self) -> ConditionLanguage | None:
        return self._condition_language

    @property
    def max_loop_count(self) -> MaxLoopCount | None:
        return self._max_loop_count

    @property
    def timeout_seconds(self) -> TransitionTimeoutSeconds | None:
        return self._timeout_seconds

    @property
    def retry_count(self) -> RetryCount | None:
        return self._retry_count

    @property
    def retry_delay_seconds(self) -> TransitionRetryDelay | None:
        return self._retry_delay_seconds

    @property
    def data_mapping(self) -> DataMapping | None:
        return self._data_mapping

    @property
    def label(self) -> TransitionLabel | None:
        return self._label
