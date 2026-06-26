from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.value_objects.ids import (
    GraphDefinitionId,
    GraphNodeDefinitionId,
    GraphNodeTransitionDefinitionId,
)
from shell.domain.platform.value_objects.edge_type import EdgeType
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    pass


class GraphNodeTransitionDefinition(Entity[GraphNodeTransitionDefinitionId]):
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
        priority: int = 0,
        condition_expression: str | None = None,
        condition_language: str | None = None,
        max_loop_count: int = 0,
        timeout_seconds: int | None = None,
        retry_count: int = 0,
        retry_delay_seconds: int = 0,
        data_mapping: dict[str, str] | None = None,
        label: str = "",
    ) -> None:
        if transition_type == EdgeType.CONDITIONAL and not condition_expression:
            raise ValueError("CONDITIONAL transition requires condition_expression")
        super().__init__(id)
        self._graph_definition_id = graph_definition_id
        self._source_node_definition_id = source_node_definition_id
        self._target_node_definition_id = target_node_definition_id
        self._transition_type = transition_type
        self._priority = priority
        self._condition_expression = condition_expression
        self._condition_language = condition_language
        self._max_loop_count = max_loop_count
        self._timeout_seconds = timeout_seconds
        self._retry_count = retry_count
        self._retry_delay_seconds = retry_delay_seconds
        self._data_mapping = data_mapping
        self._label = label

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
    def priority(self) -> int:
        return self._priority

    @property
    def condition_expression(self) -> str | None:
        return self._condition_expression

    @property
    def condition_language(self) -> str | None:
        return self._condition_language

    @property
    def max_loop_count(self) -> int:
        return self._max_loop_count

    @property
    def timeout_seconds(self) -> int | None:
        return self._timeout_seconds

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @property
    def retry_delay_seconds(self) -> int:
        return self._retry_delay_seconds

    @property
    def data_mapping(self) -> dict[str, str] | None:
        return self._data_mapping

    @property
    def label(self) -> str:
        return self._label
