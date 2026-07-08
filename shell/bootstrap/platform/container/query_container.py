"""Kontener obsługujący wyłącznie operacje odczytu (Query Handlers)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from dependency_injector import containers, providers

from shell.application.definition.graph_definition.query_handlers.graph_definition_get_by_id_handler import (
    GraphDefinitionGetByIdHandler,
)
from shell.application.definition.node_definition.query_handlers.node_definition_get_by_id_handler import (
    NodeDefinitionGetByIdHandler,
)
from shell.application.definition.rag_document.query_handlers.rag_document_get_by_id_handler import (
    RagDocumentGetByIdHandler,
)
from shell.application.definition.rag_document.query_handlers.rag_search_similar_handler import (
    RagSearchSimilarHandler,
)
from shell.application.definition.runner_config.query_handlers.runner_config_get_by_id_handler import (
    RunnerConfigGetByIdHandler,
)
from shell.application.definition.runner_config.query_handlers.runner_config_get_handler import (
    RunnerConfigGetHandler,
)
from shell.application.execution.agent_config_execution.query_handlers.agent_config_execution_get_by_id_handler import (
    AgentConfigExecutionGetByIdHandler,
)
from shell.application.execution.agent_execution.query_handlers.agent_execution_get_by_id_handler import (
    AgentExecutionGetByIdHandler,
)
from shell.application.execution.agent_skill_execution.query_handlers.agent_skill_execution_get_by_id_handler import (
    AgentSkillExecutionGetByIdHandler,
)
from shell.application.execution.edge_execution.query_handlers.edge_execution_get_by_id_handler import (
    EdgeExecutionGetByIdHandler,
)
from shell.application.execution.graph_execution.query_handlers.graph_execution_get_by_id_handler import (
    GraphExecutionGetByIdHandler,
)
from shell.application.execution.node_execution.query_handlers.node_execution_get_by_id_handler import (
    NodeExecutionGetByIdHandler,
)
from shell.application.execution.node_execution.query_handlers.node_execution_get_result_handler import (
    NodeExecutionGetResultHandler,
)
from shell.application.execution.session_execution.query_handlers.session_get_history_handler import (
    SessionGetHistoryHandler,
)
from shell.application.execution.task_execution.query_handlers.task_execution_get_by_id_handler import (
    TaskExecutionGetByIdHandler,
)
from shell.application.execution.task_execution.query_handlers.task_execution_get_by_name_handler import (
    TaskExecutionGetByNameHandler,
)
from shell.application.execution.task_execution.query_handlers.task_execution_get_current_handler import (
    TaskExecutionGetCurrentHandler,
)
from shell.application.execution.user_execution.query_handlers.user_execution_get_by_id_handler import (
    UserExecutionGetByIdHandler,
)
from shell.application.execution.workflow.query_handlers.workflow_get_by_id_handler import (
    WorkflowGetByIdHandler,
)
from shell.application.execution.workflow.query_handlers.workflow_state_get_by_id_handler import (
    WorkflowStateGetByIdHandler,
)
from shell.application.messaging.query_handlers.message_get_by_id_handler import (
    MessageGetByIdHandler,
)
from shell.application.project.project.query_handlers.project_get_by_id_handler import (
    ProjectGetByIdHandler,
)
from shell.application.project.project_skill.query_handlers.project_skill_get_by_id_handler import (
    ProjectSkillGetByIdHandler,
)
from shell.application.scheduling.scheduler_definition.query_handlers.scheduler_definition_get_by_id_handler import (
    SchedulerDefinitionGetByIdHandler,
)
from shell.application.scheduling.scheduler_execution.query_handlers.scheduler_execution_get_by_id_handler import (
    SchedulerExecutionGetByIdHandler,
)
from shell.application.session.session_state.query_handlers.session_state_get_by_id_handler import (
    SessionStateGetByIdHandler,
)
from shell.application.user.user.query_handlers.user_get_by_id_handler import (
    UserGetByIdHandler,
)
from shell.application.user.user_skill.query_handlers.user_skill_get_by_id_handler import (
    UserSkillGetByIdHandler,
)
from shell.application.user.user_state.query_handlers.user_state_get_by_id_handler import (
    UserStateGetByIdHandler,
)

if TYPE_CHECKING:
    from dependency_injector.providers import Factory

    class _QueryContainerProtocol(Protocol):
        get_graph_definition_handler_factory: Factory[GraphDefinitionGetByIdHandler]
        get_node_definition_handler_factory: Factory[NodeDefinitionGetByIdHandler]
        get_rag_document_handler_factory: Factory[RagDocumentGetByIdHandler]
        get_runner_config_handler_factory: Factory[RunnerConfigGetByIdHandler]
        get_runner_config_by_package_handler_factory: Factory[RunnerConfigGetHandler]
        get_agent_config_execution_handler_factory: Factory[AgentConfigExecutionGetByIdHandler]
        get_agent_execution_handler_factory: Factory[AgentExecutionGetByIdHandler]
        get_agent_skill_execution_handler_factory: Factory[AgentSkillExecutionGetByIdHandler]
        get_edge_execution_handler_factory: Factory[EdgeExecutionGetByIdHandler]
        get_graph_execution_handler_factory: Factory[GraphExecutionGetByIdHandler]
        get_node_execution_handler_factory: Factory[NodeExecutionGetByIdHandler]
        get_node_execution_result_handler_factory: Factory[NodeExecutionGetResultHandler]
        get_session_history_handler_factory: Factory[SessionGetHistoryHandler]
        get_task_execution_handler_factory: Factory[TaskExecutionGetByIdHandler]
        get_task_execution_by_name_handler_factory: Factory[TaskExecutionGetByNameHandler]
        get_current_task_execution_handler_factory: Factory[TaskExecutionGetCurrentHandler]
        get_user_execution_handler_factory: Factory[UserExecutionGetByIdHandler]
        get_workflow_handler_factory: Factory[WorkflowGetByIdHandler]
        get_workflow_state_handler_factory: Factory[WorkflowStateGetByIdHandler]
        get_message_handler_factory: Factory[MessageGetByIdHandler]
        get_project_handler_factory: Factory[ProjectGetByIdHandler]
        get_project_skill_handler_factory: Factory[ProjectSkillGetByIdHandler]
        get_scheduler_definition_handler_factory: Factory[SchedulerDefinitionGetByIdHandler]
        get_scheduler_execution_handler_factory: Factory[SchedulerExecutionGetByIdHandler]
        get_session_state_handler_factory: Factory[SessionStateGetByIdHandler]
        get_user_handler_factory: Factory[UserGetByIdHandler]
        get_user_skill_handler_factory: Factory[UserSkillGetByIdHandler]
        get_user_state_handler_factory: Factory[UserStateGetByIdHandler]
        search_similar_handler_factory: Factory[RagSearchSimilarHandler]


class QueryContainer(containers.DeclarativeContainer):
    """Kontener obsługujący wyłącznie operacje odczytu (Query Handlers)."""

    infra = providers.DependenciesContainer()

    get_graph_definition_handler_factory = providers.Factory(
        GraphDefinitionGetByIdHandler, queries=infra.graph_definition_query_service_factory
    )
    get_node_definition_handler_factory = providers.Factory(
        NodeDefinitionGetByIdHandler, queries=infra.node_definition_query_service
    )
    get_rag_document_handler_factory = providers.Factory(
        RagDocumentGetByIdHandler, queries=infra.rag_query_service
    )
    get_runner_config_handler_factory = providers.Factory(
        RunnerConfigGetByIdHandler, queries=infra.runner_config_query_service
    )
    get_runner_config_by_package_handler_factory = providers.Factory(
        RunnerConfigGetHandler, queries=infra.runner_config_query_service
    )
    get_agent_config_execution_handler_factory = providers.Factory(
        AgentConfigExecutionGetByIdHandler, queries=infra.agent_config_execution_query_service
    )
    get_agent_execution_handler_factory = providers.Factory(
        AgentExecutionGetByIdHandler, queries=infra.agent_execution_query_service
    )
    get_agent_skill_execution_handler_factory = providers.Factory(
        AgentSkillExecutionGetByIdHandler, queries=infra.agent_skill_execution_query_service
    )
    get_edge_execution_handler_factory = providers.Factory(
        EdgeExecutionGetByIdHandler, queries=infra.edge_execution_query_service
    )
    get_graph_execution_handler_factory = providers.Factory(
        GraphExecutionGetByIdHandler, queries=infra.graph_execution_query_service
    )
    get_node_execution_handler_factory = providers.Factory(
        NodeExecutionGetByIdHandler, queries=infra.node_result_query_service
    )
    get_node_execution_result_handler_factory = providers.Factory(
        NodeExecutionGetResultHandler, queries=infra.node_result_query_service
    )
    get_session_history_handler_factory = providers.Factory(
        SessionGetHistoryHandler, queries=infra.session_query_http_service
    )
    get_task_execution_handler_factory = providers.Factory(
        TaskExecutionGetByIdHandler, queries=infra.task_execution_query_service
    )
    get_task_execution_by_name_handler_factory = providers.Factory(
        TaskExecutionGetByNameHandler, queries=infra.task_execution_query_service
    )
    get_current_task_execution_handler_factory = providers.Factory(
        TaskExecutionGetCurrentHandler, queries=infra.task_execution_query_service
    )
    get_user_execution_handler_factory = providers.Factory(
        UserExecutionGetByIdHandler, queries=infra.user_execution_query_service
    )
    get_workflow_handler_factory = providers.Factory(
        WorkflowGetByIdHandler, queries=infra.workflow_query_service
    )
    get_workflow_state_handler_factory = providers.Factory(
        WorkflowStateGetByIdHandler, queries=infra.workflow_state_query_service
    )
    get_message_handler_factory = providers.Factory(
        MessageGetByIdHandler, queries=infra.message_query_service
    )
    get_project_handler_factory = providers.Factory(
        ProjectGetByIdHandler, queries=infra.project_query_service
    )
    get_project_skill_handler_factory = providers.Factory(
        ProjectSkillGetByIdHandler, queries=infra.project_skill_query_service
    )
    get_scheduler_definition_handler_factory = providers.Factory(
        SchedulerDefinitionGetByIdHandler, queries=infra.scheduler_definition_query_service
    )
    get_scheduler_execution_handler_factory = providers.Factory(
        SchedulerExecutionGetByIdHandler, queries=infra.scheduler_execution_query_service
    )
    get_session_state_handler_factory = providers.Factory(
        SessionStateGetByIdHandler, queries=infra.session_state_query_service
    )
    get_user_handler_factory = providers.Factory(
        UserGetByIdHandler, queries=infra.user_query_service
    )
    get_user_skill_handler_factory = providers.Factory(
        UserSkillGetByIdHandler, queries=infra.user_skill_query_service
    )
    get_user_state_handler_factory = providers.Factory(
        UserStateGetByIdHandler, queries=infra.user_state_query_service
    )
    search_similar_handler_factory = providers.Factory(
        RagSearchSimilarHandler, queries=infra.rag_query_service, embedder=infra.embedder
    )
