"""Rejestracja Query Handlers na QueryBus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.graph_definition.queries.get_graph_definition_by_id_query import (
    GetGraphDefinitionByIdQuery,
)
from shell.application.definition.node_definition.queries.get_node_definition_by_id_query import (
    GetNodeDefinitionByIdQuery,
)
from shell.application.definition.runner_config.queries.get_runner_config_by_id_query import (
    GetRunnerConfigByIdQuery,
)
from shell.application.execution.agent_config_execution.queries.get_agent_config_execution_by_id_query import (
    GetAgentConfigExecutionByIdQuery,
)
from shell.application.execution.agent_execution.queries.get_agent_execution_by_id_query import (
    GetAgentExecutionByIdQuery,
)
from shell.application.execution.agent_skill_execution.queries.get_agent_skill_execution_by_id_query import (
    GetAgentSkillExecutionByIdQuery,
)
from shell.application.execution.edge_execution.queries.get_edge_execution_by_id_query import (
    GetEdgeExecutionByIdQuery,
)
from shell.application.execution.edge_link_execution.queries.get_edge_link_execution_by_id_query import (
    GetEdgeLinkExecutionByIdQuery,
)
from shell.application.execution.graph_execution.queries.get_graph_execution_by_id_query import (
    GetGraphExecutionByIdQuery,
)
from shell.application.execution.node_execution.queries.get_node_execution_by_id_query import (
    GetNodeExecutionByIdQuery,
)
from shell.application.execution.node_execution.queries.get_node_execution_result_query import (
    GetNodeExecutionResultQuery,
)
from shell.application.execution.task_execution.queries import (
    GetTaskExecutionByIdQuery,
    GetTaskExecutionByNameQuery,
    GetTaskExecutionCurrentQuery,
)
from shell.application.execution.task_execution.queries.list_task_executions_query import (
    ListTaskExecutionsQuery,
)
from shell.application.execution.user_execution.queries.get_user_execution_by_id_query import (
    GetUserExecutionByIdQuery,
)
from shell.application.execution.workflow.queries.get_workflow_by_id_query import (
    GetWorkflowByIdQuery,
)
from shell.application.execution.workflow.queries.get_workflow_state_by_id_query import (
    GetWorkflowStateByIdQuery,
)
from shell.application.execution.workflow.queries.list_workflows_query import (
    ListWorkflowsQuery,
)
from shell.application.messaging.message_router.queries.get_message_by_id_query import (
    GetMessageByIdQuery,
)
from shell.application.project.project.queries.get_project_by_id_query import (
    GetProjectByIdQuery,
)
from shell.application.project.project.queries.list_projects_query import (
    ListProjectsQuery,
)
from shell.application.project.project_skill.queries.get_project_skill_by_id_query import (
    GetProjectSkillByIdQuery,
)
from shell.application.scheduling.scheduler_definition.queries.get_scheduler_definition_by_id_query import (
    GetSchedulerDefinitionByIdQuery,
)
from shell.application.scheduling.scheduler_execution.queries.get_scheduler_execution_by_id_query import (
    GetSchedulerExecutionByIdQuery,
)
from shell.application.session.session.queries.get_session_history_query import (
    GetSessionHistoryQuery,
)
from shell.application.session.session.queries.list_sessions_query import ListSessionsQuery
from shell.application.session.session_state.queries.get_session_state_by_id_query import (
    GetSessionStateByIdQuery,
)
from shell.application.user.auth_session.queries.get_current_auth_session_query import (
    GetCurrentAuthSessionQuery,
)
from shell.application.user.user.queries.get_user_by_email_query import (
    GetUserByEmailQuery,
)
from shell.application.user.user.queries.get_user_by_id_query import (
    GetUserByIdQuery,
)
from shell.application.user.user.queries.list_users_query import (
    ListUsersQuery,
)
from shell.application.user.user_skill.queries.get_user_skill_by_id_query import (
    GetUserSkillByIdQuery,
)
from shell.application.user.user_state.queries.get_user_state_by_id_query import (
    GetUserStateByIdQuery,
)

if TYPE_CHECKING:
    from shell.platform.bootstrap.container.core_container import Container


def register_queries(container: Container) -> None:
    """Rejestruje wszystkie Query Handlers na QueryBus kontenera."""

    q_bus = container.app.buses.query_bus
    queries = container.app.queries

    q_bus.register(GetGraphDefinitionByIdQuery, queries.get_graph_definition_handler_factory)
    q_bus.register(GetTaskExecutionByIdQuery, queries.get_task_execution_handler_factory)
    q_bus.register(GetNodeExecutionByIdQuery, queries.get_node_execution_handler_factory)
    q_bus.register(GetNodeExecutionResultQuery, queries.get_node_execution_result_handler_factory)
    q_bus.register(GetRunnerConfigByIdQuery, queries.get_runner_config_handler_factory)
    q_bus.register(GetMessageByIdQuery, queries.get_message_handler_factory)
    q_bus.register(GetTaskExecutionByNameQuery, queries.get_task_execution_by_name_handler_factory)
    q_bus.register(GetTaskExecutionCurrentQuery, queries.get_task_execution_current_handler_factory)
    q_bus.register(GetWorkflowByIdQuery, queries.get_workflow_handler_factory)
    q_bus.register(ListWorkflowsQuery, queries.list_workflows_handler_factory)
    q_bus.register(ListUsersQuery, queries.list_users_handler_factory)
    q_bus.register(ListProjectsQuery, queries.list_projects_handler_factory)
    q_bus.register(ListTaskExecutionsQuery, queries.list_task_executions_handler_factory)
    q_bus.register(GetWorkflowStateByIdQuery, queries.get_workflow_state_handler_factory)
    q_bus.register(GetSessionHistoryQuery, queries.get_session_history_handler_factory)
    q_bus.register(ListSessionsQuery, queries.list_sessions_handler_factory)
    q_bus.register(GetGraphExecutionByIdQuery, queries.get_graph_execution_handler_factory)
    q_bus.register(GetUserByIdQuery, queries.get_user_handler_factory)
    q_bus.register(GetUserByEmailQuery, queries.get_user_by_email_handler_factory)
    q_bus.register(GetCurrentAuthSessionQuery, queries.get_current_auth_session_handler_factory)
    q_bus.register(GetUserSkillByIdQuery, queries.get_user_skill_handler_factory)
    q_bus.register(GetUserStateByIdQuery, queries.get_user_state_handler_factory)
    q_bus.register(GetUserExecutionByIdQuery, queries.get_user_execution_handler_factory)
    q_bus.register(GetNodeDefinitionByIdQuery, queries.get_node_definition_handler_factory)
    q_bus.register(GetProjectByIdQuery, queries.get_project_handler_factory)
    q_bus.register(GetProjectSkillByIdQuery, queries.get_project_skill_handler_factory)
    q_bus.register(
        GetSchedulerDefinitionByIdQuery, queries.get_scheduler_definition_handler_factory
    )
    q_bus.register(GetSchedulerExecutionByIdQuery, queries.get_scheduler_execution_handler_factory)
    q_bus.register(GetEdgeExecutionByIdQuery, queries.get_edge_execution_handler_factory)
    q_bus.register(GetEdgeLinkExecutionByIdQuery, queries.get_edge_link_execution_handler_factory)
    q_bus.register(GetAgentExecutionByIdQuery, queries.get_agent_execution_handler_factory)
    q_bus.register(
        GetAgentConfigExecutionByIdQuery, queries.get_agent_config_execution_handler_factory
    )
    q_bus.register(
        GetAgentSkillExecutionByIdQuery, queries.get_agent_skill_execution_handler_factory
    )
    q_bus.register(GetSessionStateByIdQuery, queries.get_session_state_handler_factory)
