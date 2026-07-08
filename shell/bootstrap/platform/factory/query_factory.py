"""Rejestracja Query Handlers na QueryBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.application.definition.graph_definition.queries.graph_definition_get_by_id_query import (
    GraphDefinitionGetByIdQuery,
)
from shell.application.definition.node_definition.queries.node_definition_get_by_id_query import (
    NodeDefinitionGetByIdQuery,
)
from shell.application.definition.rag_document.queries.rag_document_get_by_id_query import (
    RagDocumentGetByIdQuery,
)
from shell.application.definition.rag_document.queries.rag_search_similar_query import (
    RagSearchSimilarQuery,
)
from shell.application.definition.runner_config.queries.runner_config_get_by_id_query import (
    RunnerConfigGetByIdQuery,
)
from shell.application.definition.runner_config.queries.runner_config_get_query import (
    RunnerConfigGetQuery,
)
from shell.application.execution.agent_config_execution.queries.agent_config_execution_get_by_id_query import (
    AgentConfigExecutionGetByIdQuery,
)
from shell.application.execution.agent_execution.queries.agent_execution_get_by_id_query import (
    AgentExecutionGetByIdQuery,
)
from shell.application.execution.agent_skill_execution.queries.agent_skill_execution_get_by_id_query import (
    AgentSkillExecutionGetByIdQuery,
)
from shell.application.execution.edge_execution.queries.edge_execution_get_by_id_query import (
    EdgeExecutionGetByIdQuery,
)
from shell.application.execution.graph_execution.queries.graph_execution_get_by_id_query import (
    GraphExecutionGetByIdQuery,
)
from shell.application.execution.node_execution.queries.node_execution_get_by_id_query import (
    NodeExecutionGetByIdQuery,
)
from shell.application.execution.node_execution.queries.node_execution_get_result_query import (
    NodeExecutionGetResultQuery,
)
from shell.application.execution.session_execution.queries.session_get_history_query import (
    SessionGetHistoryQuery,
)
from shell.application.execution.task_execution.queries import (
    TaskExecutionGetByIdQuery,
    TaskExecutionGetByNameQuery,
    TaskExecutionGetCurrentQuery,
)
from shell.application.execution.user_execution.queries.user_execution_get_by_id_query import (
    UserExecutionGetByIdQuery,
)
from shell.application.execution.workflow.queries.workflow_get_by_id_query import (
    WorkflowGetByIdQuery,
)
from shell.application.execution.workflow.queries.workflow_state_get_by_id_query import (
    WorkflowStateGetByIdQuery,
)
from shell.application.messaging.queries.message_get_by_id_query import (
    MessageGetByIdQuery,
)
from shell.application.project.project.queries.project_get_by_id_query import (
    ProjectGetByIdQuery,
)
from shell.application.project.project_skill.queries.project_skill_get_by_id_query import (
    ProjectSkillGetByIdQuery,
)
from shell.application.scheduling.scheduler_definition.queries.scheduler_definition_get_by_id_query import (
    SchedulerDefinitionGetByIdQuery,
)
from shell.application.scheduling.scheduler_execution.queries.scheduler_execution_get_by_id_query import (
    SchedulerExecutionGetByIdQuery,
)
from shell.application.session.session_state.queries.session_state_get_by_id_query import (
    SessionStateGetByIdQuery,
)
from shell.application.user.user.queries.user_get_by_id_query import (
    UserGetByIdQuery,
)
from shell.application.user.user_skill.queries.user_skill_get_by_id_query import (
    UserSkillGetByIdQuery,
)
from shell.application.user.user_state.queries.user_state_get_by_id_query import (
    UserStateGetByIdQuery,
)

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_queries(core_container: CoreContainer) -> None:
    """Rejestruje wszystkie Query Handlers na QueryBus kontenera."""

    app_ctx: Any = core_container.app

    q_bus = app_ctx.buses.query_bus()
    queries = app_ctx.queries

    q_bus.register(GraphDefinitionGetByIdQuery, queries.get_graph_definition_handler_factory)
    q_bus.register(TaskExecutionGetByIdQuery, queries.get_task_execution_handler_factory)
    q_bus.register(NodeExecutionGetByIdQuery, queries.get_node_execution_handler_factory)
    q_bus.register(NodeExecutionGetResultQuery, queries.get_node_execution_result_handler_factory)
    q_bus.register(RunnerConfigGetByIdQuery, queries.get_runner_config_handler_factory)
    q_bus.register(RunnerConfigGetQuery, queries.get_runner_config_by_package_handler_factory)
    q_bus.register(RagDocumentGetByIdQuery, queries.get_rag_document_handler_factory)
    q_bus.register(RagSearchSimilarQuery, queries.search_similar_handler_factory)
    q_bus.register(MessageGetByIdQuery, queries.get_message_handler_factory)
    q_bus.register(TaskExecutionGetByNameQuery, queries.get_task_execution_by_name_handler_factory)
    q_bus.register(TaskExecutionGetCurrentQuery, queries.get_current_task_execution_handler_factory)
    q_bus.register(WorkflowGetByIdQuery, queries.get_workflow_handler_factory)
    q_bus.register(WorkflowStateGetByIdQuery, queries.get_workflow_state_handler_factory)
    q_bus.register(SessionGetHistoryQuery, queries.get_session_history_handler_factory)
    q_bus.register(GraphExecutionGetByIdQuery, queries.get_graph_execution_handler_factory)
    q_bus.register(UserGetByIdQuery, queries.get_user_handler_factory)
    q_bus.register(UserSkillGetByIdQuery, queries.get_user_skill_handler_factory)
    q_bus.register(UserStateGetByIdQuery, queries.get_user_state_handler_factory)
    q_bus.register(UserExecutionGetByIdQuery, queries.get_user_execution_handler_factory)
    q_bus.register(NodeDefinitionGetByIdQuery, queries.get_node_definition_handler_factory)
    q_bus.register(ProjectGetByIdQuery, queries.get_project_handler_factory)
    q_bus.register(ProjectSkillGetByIdQuery, queries.get_project_skill_handler_factory)
    q_bus.register(SchedulerDefinitionGetByIdQuery, queries.get_scheduler_definition_handler_factory)
    q_bus.register(SchedulerExecutionGetByIdQuery, queries.get_scheduler_execution_handler_factory)
    q_bus.register(EdgeExecutionGetByIdQuery, queries.get_edge_execution_handler_factory)
    q_bus.register(AgentExecutionGetByIdQuery, queries.get_agent_execution_handler_factory)
    q_bus.register(AgentConfigExecutionGetByIdQuery, queries.get_agent_config_execution_handler_factory)
    q_bus.register(AgentSkillExecutionGetByIdQuery, queries.get_agent_skill_execution_handler_factory)
    q_bus.register(SessionStateGetByIdQuery, queries.get_session_state_handler_factory)
