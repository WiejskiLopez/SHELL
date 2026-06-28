from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.value_objects.edge_type import EdgeType

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
        GraphNodeExecution,
    )
    from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
        GraphNodeExecutionRepository,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_transition_execution.repositories.graph_node_transition_execution_repository import (
        GraphNodeTransitionExecutionRepository,
    )


class TransitionBasedGraphNodeExecutionNavigator:
    @staticmethod
    async def first_async(
        graph_execution: GraphExecution,
        node_repo: GraphNodeExecutionRepository,
        transition_repo: GraphNodeTransitionExecutionRepository,
    ) -> GraphNodeExecution | None:
        transitions = await transition_repo.list_by_graph_execution_id(graph_execution.id)
        start_transitions = [t for t in transitions if t.source_node_execution_id is None]
        if not start_transitions:
            return await TransitionBasedGraphNodeExecutionNavigator._fallback_first_async(
                graph_execution,
                node_repo,
            )
        start_transition = start_transitions[0]
        target_id = start_transition.target_node_execution_id
        if target_id is None:
            return None
        return await node_repo.get_by_id(target_id)

    @staticmethod
    async def next_after_async(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        node_repo: GraphNodeExecutionRepository,
        transition_repo: GraphNodeTransitionExecutionRepository,
    ) -> Iterable[GraphNodeExecution]:
        outgoing = await transition_repo.list_outgoing_for_node(graph_node_execution_id)
        if not outgoing:
            return []

        result_ids: list[GraphNodeExecutionId] = []
        has_default = False
        default_target_id: GraphNodeExecutionId | None = None
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

        nodes = await node_repo.list_by_ids(result_ids)
        nodes_by_id = {n.id: n for n in nodes}
        return [nodes_by_id[rid] for rid in result_ids if rid in nodes_by_id]

    @staticmethod
    async def next_conditional_async(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        node_repo: GraphNodeExecutionRepository,
        transition_repo: GraphNodeTransitionExecutionRepository,
    ) -> list[tuple[GraphNodeExecution, str]]:
        outgoing = await transition_repo.list_outgoing_for_node(graph_node_execution_id)
        target_ids: list[GraphNodeExecutionId] = []
        for t in outgoing:
            if t.target_node_execution_id is None:
                continue
            if t.edge_type == EdgeType.CONDITIONAL:
                target_ids.append(t.target_node_execution_id)
        if not target_ids:
            return []
        nodes = await node_repo.list_by_ids(target_ids)
        nodes_by_id = {n.id: n for n in nodes}
        results: list[tuple[GraphNodeExecution, str]] = []
        for t in outgoing:
            if t.target_node_execution_id is None:
                continue
            if t.edge_type == EdgeType.CONDITIONAL:
                node = nodes_by_id.get(t.target_node_execution_id)
                if node and t.condition_expression:
                    results.append((node, t.condition_expression.value))
        return results

    @staticmethod
    async def next_error_handler_async(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        node_repo: GraphNodeExecutionRepository,
        transition_repo: GraphNodeTransitionExecutionRepository,
    ) -> GraphNodeExecution | None:
        outgoing = await transition_repo.list_outgoing_for_node(graph_node_execution_id)
        for t in outgoing:
            if t.target_node_execution_id is None:
                continue
            if t.edge_type == EdgeType.ERROR_HANDLER:
                return await node_repo.get_by_id(t.target_node_execution_id)
        return None

    @staticmethod
    async def next_loop_target_async(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        node_repo: GraphNodeExecutionRepository,
        transition_repo: GraphNodeTransitionExecutionRepository,
    ) -> GraphNodeExecution | None:
        outgoing = await transition_repo.list_outgoing_for_node(graph_node_execution_id)
        for t in outgoing:
            if t.target_node_execution_id is None:
                continue
            if t.edge_type == EdgeType.LOOP:
                return await node_repo.get_by_id(t.target_node_execution_id)
        return None

    @staticmethod
    async def _fallback_first_async(
        graph_execution: GraphExecution,
        node_repo: GraphNodeExecutionRepository,
    ) -> GraphNodeExecution | None:
        nodes = await node_repo.list_by_graph_execution_id(graph_execution.id)
        if not nodes:
            return None
        ordered = sorted(nodes, key=lambda n: n.position.value)
        return ordered[0] if ordered else None
