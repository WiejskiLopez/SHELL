"""Container handling read operations only (Query Handlers)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from dependency_injector import containers, providers

from shell.application.definition.graph_definition.query_handlers.get_graph_definition_by_id_handler import (
    GetGraphDefinitionByIdHandler,
)
from shell.application.definition.node_definition.query_handlers.get_node_definition_by_id_handler import (
    GetNodeDefinitionByIdHandler,
)
from shell.application.definition.runner_config.query_handlers.get_runner_config_by_id_handler import (
    GetRunnerConfigByIdHandler,
)
from shell.application.execution.agent_config_execution.query_handlers.get_agent_config_execution_by_id_handler import (
    GetAgentConfigExecutionByIdHandler,
)
from shell.application.execution.agent_execution.query_handlers.get_agent_execution_by_id_handler import (
    GetAgentExecutionByIdHandler,
)
from shell.application.execution.agent_skill_execution.query_handlers.get_agent_skill_execution_by_id_handler import (
    GetAgentSkillExecutionByIdHandler,
)
from shell.application.execution.edge_execution.query_handlers.get_edge_execution_by_id_handler import (
    GetEdgeExecutionByIdHandler,
)
from shell.application.execution.graph_execution.query_handlers.get_graph_execution_by_id_handler import (
    GetGraphExecutionByIdHandler,
)
from shell.application.execution.node_execution.query_handlers.get_node_execution_by_id_handler import (
    GetNodeExecutionByIdHandler,
)
from shell.application.execution.node_execution.query_handlers.get_node_execution_result_handler import (
    GetNodeExecutionResultHandler,
)
from shell.application.execution.task_execution.query_handlers.get_task_execution_by_id_handler import (
    GetTaskExecutionByIdHandler,
)
from shell.application.execution.task_execution.query_handlers.get_task_execution_by_name_handler import (
    GetTaskExecutionByNameHandler,
)
from shell.application.execution.task_execution.query_handlers.get_task_execution_current_handler import (
    GetTaskExecutionCurrentHandler,
)
from shell.application.execution.user_execution.query_handlers.get_user_execution_by_id_handler import (
    GetUserExecutionByIdHandler,
)
from shell.application.execution.workflow.query_handlers.get_workflow_by_id_handler import (
    GetWorkflowByIdHandler,
)
from shell.application.execution.workflow.query_handlers.get_workflow_state_by_id_handler import (
    GetWorkflowStateByIdHandler,
)
from shell.application.messaging.message_router.query_handlers.get_message_by_id_handler import (
    GetMessageByIdHandler,
)
from shell.application.project.project.query_handlers.get_project_by_id_handler import (
    GetProjectByIdHandler,
)
from shell.application.project.project_skill.query_handlers.get_project_skill_by_id_handler import (
    GetProjectSkillByIdHandler,
)
from shell.application.scheduling.scheduler_definition.query_handlers.get_scheduler_definition_by_id_handler import (
    GetSchedulerDefinitionByIdHandler,
)
from shell.application.scheduling.scheduler_execution.query_handlers.get_scheduler_execution_by_id_handler import (
    GetSchedulerExecutionByIdHandler,
)
from shell.application.session.session.query_handlers.get_session_history_handler import (
    GetSessionHistoryHandler,
)
from shell.application.session.session.query_handlers.list_sessions_handler import (
    ListSessionsHandler,
)
from shell.application.session.session_state.query_handlers.get_session_state_by_id_handler import (
    GetSessionStateByIdHandler,
)
from shell.application.user.user.query_handlers.get_user_by_id_handler import (
    GetUserByIdHandler,
)
from shell.application.user.user_skill.query_handlers.get_user_skill_by_id_handler import (
    GetUserSkillByIdHandler,
)
from shell.application.user.user_state.query_handlers.get_user_state_by_id_handler import (
    GetUserStateByIdHandler,
)

if TYPE_CHECKING:
    from dependency_injector.providers import Factory

    class _QueryContainerProtocol(Protocol):
        get_graph_definition_handler_factory: Factory[GetGraphDefinitionByIdHandler]
        get_node_definition_handler_factory: Factory[GetNodeDefinitionByIdHandler]
        get_runner_config_handler_factory: Factory[GetRunnerConfigByIdHandler]
        get_agent_config_execution_handler_factory: Factory[GetAgentConfigExecutionByIdHandler]
        get_agent_execution_handler_factory: Factory[GetAgentExecutionByIdHandler]
        get_agent_skill_execution_handler_factory: Factory[GetAgentSkillExecutionByIdHandler]
        get_edge_execution_handler_factory: Factory[GetEdgeExecutionByIdHandler]
        get_graph_execution_handler_factory: Factory[GetGraphExecutionByIdHandler]
        get_node_execution_handler_factory: Factory[GetNodeExecutionByIdHandler]
        get_node_execution_result_handler_factory: Factory[GetNodeExecutionResultHandler]
        get_session_history_handler_factory: Factory[GetSessionHistoryHandler]
        list_sessions_handler_factory: Factory[ListSessionsHandler]
        get_task_execution_handler_factory: Factory[GetTaskExecutionByIdHandler]
        get_task_execution_by_name_handler_factory: Factory[GetTaskExecutionByNameHandler]
        get_current_task_execution_handler_factory: Factory[GetTaskExecutionCurrentHandler]
        get_user_execution_handler_factory: Factory[GetUserExecutionByIdHandler]
        get_workflow_handler_factory: Factory[GetWorkflowByIdHandler]
        get_workflow_state_handler_factory: Factory[GetWorkflowStateByIdHandler]
        get_message_handler_factory: Factory[GetMessageByIdHandler]
        get_project_handler_factory: Factory[GetProjectByIdHandler]
        get_project_skill_handler_factory: Factory[GetProjectSkillByIdHandler]
        get_scheduler_definition_handler_factory: Factory[GetSchedulerDefinitionByIdHandler]
        get_scheduler_execution_handler_factory: Factory[GetSchedulerExecutionByIdHandler]
        get_session_state_handler_factory: Factory[GetSessionStateByIdHandler]
        get_user_handler_factory: Factory[GetUserByIdHandler]
        get_user_skill_handler_factory: Factory[GetUserSkillByIdHandler]
        get_user_state_handler_factory: Factory[GetUserStateByIdHandler]


class QueryContainer(containers.DeclarativeContainer):
    """Container handling read operations only (Query Handlers)."""

    infra = providers.DependenciesContainer()

    get_graph_definition_handler_factory = providers.Factory(
        GetGraphDefinitionByIdHandler, queries=infra.graph_definition_query_service_factory
    )
    get_node_definition_handler_factory = providers.Factory(
        GetNodeDefinitionByIdHandler, queries=infra.node_definition_query_service
    )
    get_runner_config_handler_factory = providers.Factory(
        GetRunnerConfigByIdHandler, queries=infra.runner_config_query_service
    )
    get_agent_config_execution_handler_factory = providers.Factory(
        GetAgentConfigExecutionByIdHandler, queries=infra.agent_config_execution_query_service
    )
    get_agent_execution_handler_factory = providers.Factory(
        GetAgentExecutionByIdHandler, queries=infra.agent_execution_query_service
    )
    get_agent_skill_execution_handler_factory = providers.Factory(
        GetAgentSkillExecutionByIdHandler, queries=infra.agent_skill_execution_query_service
    )
    get_edge_execution_handler_factory = providers.Factory(
        GetEdgeExecutionByIdHandler, queries=infra.edge_execution_query_service
    )
    get_graph_execution_handler_factory = providers.Factory(
        GetGraphExecutionByIdHandler, queries=infra.graph_execution_query_service
    )
    get_node_execution_handler_factory = providers.Factory(
        GetNodeExecutionByIdHandler, queries=infra.node_result_query_service
    )
    get_node_execution_result_handler_factory = providers.Factory(
        GetNodeExecutionResultHandler, queries=infra.node_result_query_service
    )
    get_session_history_handler_factory = providers.Factory(
        GetSessionHistoryHandler, queries=infra.session_query_service
    )
    list_sessions_handler_factory = providers.Factory(
        ListSessionsHandler, queries=infra.session_query_service
    )
    get_task_execution_handler_factory = providers.Factory(
        GetTaskExecutionByIdHandler, queries=infra.task_execution_query_service
    )
    get_task_execution_by_name_handler_factory = providers.Factory(
        GetTaskExecutionByNameHandler, queries=infra.task_execution_query_service
    )
    get_current_task_execution_handler_factory = providers.Factory(
        GetTaskExecutionCurrentHandler, queries=infra.task_execution_query_service
    )
    get_user_execution_handler_factory = providers.Factory(
        GetUserExecutionByIdHandler, queries=infra.user_execution_query_service
    )
    get_workflow_handler_factory = providers.Factory(
        GetWorkflowByIdHandler, queries=infra.workflow_query_service
    )
    get_workflow_state_handler_factory = providers.Factory(
        GetWorkflowStateByIdHandler, queries=infra.workflow_state_query_service
    )
    get_message_handler_factory = providers.Factory(
        GetMessageByIdHandler, queries=infra.message_router_query_service
    )
    get_project_handler_factory = providers.Factory(
        GetProjectByIdHandler, queries=infra.project_query_service
    )
    get_project_skill_handler_factory = providers.Factory(
        GetProjectSkillByIdHandler, queries=infra.project_skill_query_service
    )
    get_scheduler_definition_handler_factory = providers.Factory(
        GetSchedulerDefinitionByIdHandler, queries=infra.scheduler_definition_query_service
    )
    get_scheduler_execution_handler_factory = providers.Factory(
        GetSchedulerExecutionByIdHandler, queries=infra.scheduler_execution_query_service
    )
    get_session_state_handler_factory = providers.Factory(
        GetSessionStateByIdHandler, queries=infra.session_state_query_service
    )
    get_user_handler_factory = providers.Factory(
        GetUserByIdHandler, queries=infra.user_query_service
    )
    get_user_skill_handler_factory = providers.Factory(
        GetUserSkillByIdHandler, queries=infra.user_skill_query_service
    )
    get_user_state_handler_factory = providers.Factory(
        GetUserStateByIdHandler, queries=infra.user_state_query_service
    )
