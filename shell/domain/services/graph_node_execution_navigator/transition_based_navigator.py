from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.value_objects.transition_type import TransitionType

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.aggregates.graph_execution import GraphExecution
    from shell.domain.entities.graph_node_execution import GraphNodeExecution
    from shell.domain.value_objects.ids import GraphNodeExecutionId


class TransitionBasedNavigator:
    def first(self, graph_execution: GraphExecution) -> GraphNodeExecution | None:
        nodes_by_id = {n.id.value: n for n in graph_execution.graph_node_executions}
        transitions = graph_execution.transitions

        if not transitions:
            return self._fallback_first(graph_execution)

        start_transitions = [
            t for t in transitions if t.source_node_execution_id is None
        ]

        if not start_transitions:
            return self._fallback_first(graph_execution)

        start_transition = min(start_transitions, key=lambda t: t.priority)
        target_id = start_transition.target_node_execution_id.value
        return nodes_by_id.get(target_id)

    def next_after(
        self,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> Iterable[GraphNodeExecution]:
        nodes_by_id = {n.id.value: n for n in graph_execution.graph_node_executions}
        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)

        if not outgoing:
            return []

        matched: list[GraphNodeExecution] = []
        has_default = False
        default_target: GraphNodeExecution | None = None

        for t in outgoing:
            if t.transition_type == TransitionType.DEFAULT:
                has_default = True
                default_target = nodes_by_id.get(t.target_node_execution_id.value)
                continue

            if t.transition_type == TransitionType.PARALLEL:
                node = nodes_by_id.get(t.target_node_execution_id.value)
                if node:
                    matched.append(node)
                continue

            if t.transition_type == TransitionType.SEQUENCE:
                node = nodes_by_id.get(t.target_node_execution_id.value)
                if node:
                    matched.append(node)
                continue

        if not matched and has_default and default_target:
            matched.append(default_target)

        return matched

    @staticmethod
    def _fallback_first(graph_execution: GraphExecution) -> GraphNodeExecution | None:
        ordered = sorted(graph_execution.graph_node_executions, key=lambda n: n.position)
        return ordered[0] if ordered else None
