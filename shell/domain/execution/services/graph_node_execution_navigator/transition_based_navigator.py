from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.value_objects.edge_type import EdgeType

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
        GraphNodeExecution,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
        GraphNodeExecutionRepository,
    )


class TransitionBasedGraphNodeExecutionNavigator:
    @staticmethod
    def first(graph_execution: GraphExecution) -> GraphNodeExecution | None:
        nodes_by_id = {n.id.value: n for n in graph_execution.graph_node_executions}
        transitions = graph_execution.transitions

        if not transitions:
            return TransitionBasedGraphNodeExecutionNavigator._fallback_first(graph_execution)

        start_transitions = [t for t in transitions if not t.source_node_execution_id]
        if not start_transitions:
            return TransitionBasedGraphNodeExecutionNavigator._fallback_first(graph_execution)

        start_transition = min(start_transitions, key=lambda t: t.priority)
        target_id = start_transition.target_node_execution_id
        if target_id is None:
            return None
        return nodes_by_id.get(target_id)

    @staticmethod
    def next_after(
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
            if t.target_node_execution_id is None:
                continue
            if t.edge_type == EdgeType.DEFAULT:
                has_default = True
                default_target = nodes_by_id.get(t.target_node_execution_id)
                continue
            if t.edge_type == EdgeType.SEQUENCE:
                node = nodes_by_id.get(t.target_node_execution_id)
                if node:
                    matched.append(node)
                continue

        if not matched and has_default and default_target:
            matched.append(default_target)

        return matched

    @staticmethod
    def next_conditional(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> list[tuple[GraphNodeExecution, str]]:
        nodes_by_id = {n.id.value: n for n in graph_execution.graph_node_executions}
        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)
        results: list[tuple[GraphNodeExecution, str]] = []
        for t in outgoing:
            if t.target_node_execution_id is None:
                continue
            if t.edge_type == EdgeType.CONDITIONAL:
                node = nodes_by_id.get(t.target_node_execution_id)
                if node and t.condition_expression:
                    results.append((node, t.condition_expression))
        return results

    @staticmethod
    def next_error_handler(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> GraphNodeExecution | None:
        nodes_by_id = {n.id.value: n for n in graph_execution.graph_node_executions}
        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)
        for t in outgoing:
            if t.target_node_execution_id is None:
                continue
            if t.edge_type == EdgeType.ERROR_HANDLER:
                return nodes_by_id.get(t.target_node_execution_id)
        return None

    @staticmethod
    def next_loop_target(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> GraphNodeExecution | None:
        nodes_by_id = {n.id.value: n for n in graph_execution.graph_node_executions}
        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)
        for t in outgoing:
            if t.target_node_execution_id is None:
                continue
            if t.edge_type == EdgeType.LOOP:
                return nodes_by_id.get(t.target_node_execution_id)
        return None

    # ── Async variants (use GraphNodeExecutionRepository) ────────────────────

    @staticmethod
    async def first_async(
        graph_execution: GraphExecution,
        node_repo: GraphNodeExecutionRepository,
    ) -> GraphNodeExecution | None:
        from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
            GraphNodeExecutionId,
        )

        transitions = graph_execution.transitions
        if not transitions:
            return await TransitionBasedGraphNodeExecutionNavigator._fallback_first_async(
                graph_execution,
                node_repo,
            )
        start_transitions = [t for t in transitions if not t.source_node_execution_id]
        if not start_transitions:
            return await TransitionBasedGraphNodeExecutionNavigator._fallback_first_async(
                graph_execution,
                node_repo,
            )
        start_transition = min(start_transitions, key=lambda t: t.priority)
        target_id = start_transition.target_node_execution_id
        if target_id is None:
            return None
        return await node_repo.get_by_id(GraphNodeExecutionId(target_id))

    @staticmethod
    async def next_after_async(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        node_repo: GraphNodeExecutionRepository,
    ) -> Iterable[GraphNodeExecution]:
        from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
            GraphNodeExecutionId,
        )

        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)
        if not outgoing:
            return []

        result_ids: list[str] = []
        has_default = False
        default_target_id: str | None = None
        for t in outgoing:
            if t.target_node_execution_id is None:
                continue
            tid = t.target_node_execution_id
            if t.edge_type == EdgeType.DEFAULT:
                has_default = True
                default_target_id = tid
                continue
            if t.edge_type == EdgeType.SEQUENCE:
                result_ids.append(tid)
        if not result_ids and has_default and default_target_id:
            result_ids.append(default_target_id)
        if not result_ids:
            return []

        ids = [GraphNodeExecutionId(rid) for rid in result_ids]
        nodes = await node_repo.list_by_ids(ids)
        nodes_by_id = {n.id.value: n for n in nodes}
        return [nodes_by_id[rid] for rid in result_ids if rid in nodes_by_id]

    @staticmethod
    async def _fallback_first_async(
        graph_execution: GraphExecution,
        node_repo: GraphNodeExecutionRepository,
    ) -> GraphNodeExecution | None:
        node_ids = list(graph_execution.graph_node_execution_ids)
        if not node_ids:
            return None
        nodes = await node_repo.list_by_ids(node_ids)
        ordered = sorted(nodes, key=lambda n: n.position)
        return ordered[0] if ordered else None

    @staticmethod
    def _fallback_first(graph_execution: GraphExecution) -> GraphNodeExecution | None:
        ordered = sorted(graph_execution.graph_node_executions, key=lambda n: n.position)
        return ordered[0] if ordered else None
