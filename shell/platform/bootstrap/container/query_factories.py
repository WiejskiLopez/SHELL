"""Pure-DI factories for application query handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
from shell.application.execution.node_execution.query_handlers.get_node_execution_result_handler import (
    GetNodeExecutionResultHandler,
)
from shell.application.execution.task_execution.query_handlers.get_task_execution_by_name_handler import (
    GetTaskExecutionByNameHandler,
)
from shell.application.execution.task_execution.query_handlers.get_task_execution_current_handler import (
    GetTaskExecutionCurrentHandler,
)
from shell.application.execution.task_execution.query_handlers.list_task_executions_handler import (
    ListTaskExecutionsHandler,
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
from shell.application.execution.workflow.query_handlers.list_workflows_handler import (
    ListWorkflowsHandler,
)
from shell.application.project.project.query_handlers.get_project_by_id_handler import (
    GetProjectByIdHandler,
)
from shell.application.project.project.query_handlers.list_projects_handler import (
    ListProjectsHandler,
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
from shell.application.user.user.query_handlers.get_user_by_email_handler import (
    GetUserByEmailHandler,
)
from shell.application.user.user.query_handlers.get_user_by_id_handler import GetUserByIdHandler
from shell.application.user.user_skill.query_handlers.get_user_skill_by_id_handler import (
    GetUserSkillByIdHandler,
)

if TYPE_CHECKING:
    from shell.application.definition.graph_definition.query_handlers.get_graph_definition_by_id_handler import (
        GetGraphDefinitionByIdHandler,
    )
    from shell.application.definition.node_definition.query_handlers.get_node_definition_by_id_handler import (
        GetNodeDefinitionByIdHandler,
    )
    from shell.application.execution.edge_link_execution.query_handlers.get_edge_link_execution_by_id_handler import (
        GetEdgeLinkExecutionByIdHandler,
    )
    from shell.application.execution.node_execution.query_handlers.get_node_execution_by_id_handler import (
        GetNodeExecutionByIdHandler,
    )
    from shell.application.execution.task_execution.query_handlers.get_task_execution_by_id_handler import (
        GetTaskExecutionByIdHandler,
    )
    from shell.application.messaging.message_router.query_handlers.get_message_by_id_handler import (
        GetMessageByIdHandler,
    )
    from shell.application.user.auth_session.query_handlers.get_current_auth_session_handler import (
        GetCurrentAuthSessionHandler,
    )
    from shell.application.user.user.query_handlers.list_users_handler import ListUsersHandler
    from shell.application.user.user_state.query_handlers.get_user_state_by_id_handler import (
        GetUserStateByIdHandler,
    )
    from shell.platform.bootstrap.container.infrastructure import Infrastructure


class Queries:
    """Container for query handler factories."""

    def __init__(self, infra: Infrastructure) -> None:
        self._infra = infra

    def get_graph_definition_handler_factory(self) -> GetGraphDefinitionByIdHandler:
        from shell.application.definition.graph_definition.query_handlers.get_graph_definition_by_id_handler import (
            GetGraphDefinitionByIdHandler,
        )

        return GetGraphDefinitionByIdHandler(
            queries=self._infra.graph_definition_query_service_factory()
        )

    def get_task_execution_handler_factory(self) -> GetTaskExecutionByIdHandler:
        from shell.application.execution.task_execution.query_handlers.get_task_execution_by_id_handler import (
            GetTaskExecutionByIdHandler,
        )

        return GetTaskExecutionByIdHandler(queries=self._infra.task_execution_query_service)

    def get_node_execution_handler_factory(self) -> GetNodeExecutionByIdHandler:
        from shell.application.execution.node_execution.query_handlers.get_node_execution_by_id_handler import (
            GetNodeExecutionByIdHandler,
        )

        return GetNodeExecutionByIdHandler(queries=self._infra.node_result_query_service)

    def get_node_execution_result_handler_factory(self) -> GetNodeExecutionResultHandler:
        return GetNodeExecutionResultHandler(queries=self._infra.node_result_query_service)

    def get_runner_config_handler_factory(self) -> GetRunnerConfigByIdHandler:
        return GetRunnerConfigByIdHandler(queries=self._infra.runner_config_query_service)

    def get_task_execution_by_name_handler_factory(self) -> GetTaskExecutionByNameHandler:
        return GetTaskExecutionByNameHandler(queries=self._infra.task_execution_query_service)

    def get_task_execution_current_handler_factory(self) -> GetTaskExecutionCurrentHandler:
        return GetTaskExecutionCurrentHandler(queries=self._infra.task_execution_query_service)

    def get_workflow_handler_factory(self) -> GetWorkflowByIdHandler:
        return GetWorkflowByIdHandler(queries=self._infra.workflow_query_service)

    def list_workflows_handler_factory(self) -> ListWorkflowsHandler:
        return ListWorkflowsHandler(queries=self._infra.workflow_query_service)

    def list_users_handler_factory(self) -> ListUsersHandler:
        from shell.application.user.user.query_handlers.list_users_handler import ListUsersHandler

        return ListUsersHandler(queries=self._infra.user_query_service)

    def list_projects_handler_factory(self) -> ListProjectsHandler:
        return ListProjectsHandler(queries=self._infra.project_query_service)

    def list_task_executions_handler_factory(self) -> ListTaskExecutionsHandler:
        return ListTaskExecutionsHandler(queries=self._infra.task_execution_query_service)

    def get_workflow_state_handler_factory(self) -> GetWorkflowStateByIdHandler:
        return GetWorkflowStateByIdHandler(queries=self._infra.workflow_state_query_service)

    def get_session_history_handler_factory(self) -> GetSessionHistoryHandler:
        return GetSessionHistoryHandler(queries=self._infra.session_query_service)

    def list_sessions_handler_factory(self) -> ListSessionsHandler:
        return ListSessionsHandler(queries=self._infra.session_query_service)

    def get_graph_execution_handler_factory(self) -> GetGraphExecutionByIdHandler:
        return GetGraphExecutionByIdHandler(queries=self._infra.graph_execution_query_service)

    def get_user_handler_factory(self) -> GetUserByIdHandler:
        return GetUserByIdHandler(queries=self._infra.user_query_service)

    def get_user_by_email_handler_factory(self) -> GetUserByEmailHandler:
        return GetUserByEmailHandler(queries=self._infra.user_query_service)

    def get_current_auth_session_handler_factory(self) -> GetCurrentAuthSessionHandler:
        from shell.application.user.auth_session.query_handlers.get_current_auth_session_handler import (
            GetCurrentAuthSessionHandler,
        )

        return GetCurrentAuthSessionHandler(
            queries=self._infra.auth_session_query_service,
            clock=self._infra.clock_factory(),
        )

    def get_user_skill_handler_factory(self) -> GetUserSkillByIdHandler:
        return GetUserSkillByIdHandler(queries=self._infra.user_skill_query_service)

    def get_user_state_handler_factory(self) -> GetUserStateByIdHandler:
        from shell.application.user.user_state.query_handlers.get_user_state_by_id_handler import (
            GetUserStateByIdHandler,
        )

        return GetUserStateByIdHandler(queries=self._infra.user_state_query_service)

    def get_user_execution_handler_factory(self) -> GetUserExecutionByIdHandler:
        return GetUserExecutionByIdHandler(queries=self._infra.user_execution_query_service)

    def get_node_definition_handler_factory(self) -> GetNodeDefinitionByIdHandler:
        from shell.application.definition.node_definition.query_handlers.get_node_definition_by_id_handler import (
            GetNodeDefinitionByIdHandler,
        )

        return GetNodeDefinitionByIdHandler(queries=self._infra.node_definition_query_service)

    def get_message_handler_factory(self) -> GetMessageByIdHandler:
        from shell.application.messaging.message_router.query_handlers.get_message_by_id_handler import (
            GetMessageByIdHandler,
        )

        return GetMessageByIdHandler(queries=self._infra.message_router_query_service)

    def get_project_handler_factory(self) -> GetProjectByIdHandler:
        return GetProjectByIdHandler(queries=self._infra.project_query_service)

    def get_project_skill_handler_factory(self) -> GetProjectSkillByIdHandler:
        return GetProjectSkillByIdHandler(queries=self._infra.project_skill_query_service)

    def get_scheduler_definition_handler_factory(self) -> GetSchedulerDefinitionByIdHandler:
        return GetSchedulerDefinitionByIdHandler(
            queries=self._infra.scheduler_definition_query_service
        )

    def get_scheduler_execution_handler_factory(self) -> GetSchedulerExecutionByIdHandler:
        return GetSchedulerExecutionByIdHandler(
            queries=self._infra.scheduler_execution_query_service
        )

    def get_edge_execution_handler_factory(self) -> GetEdgeExecutionByIdHandler:
        return GetEdgeExecutionByIdHandler(queries=self._infra.edge_execution_query_service)

    def get_edge_link_execution_handler_factory(self) -> GetEdgeLinkExecutionByIdHandler:
        from shell.application.execution.edge_link_execution.query_handlers.get_edge_link_execution_by_id_handler import (
            GetEdgeLinkExecutionByIdHandler,
        )

        return GetEdgeLinkExecutionByIdHandler(
            queries=self._infra.edge_link_execution_query_service
        )

    def get_agent_execution_handler_factory(self) -> GetAgentExecutionByIdHandler:
        return GetAgentExecutionByIdHandler(queries=self._infra.agent_execution_query_service)

    def get_agent_config_execution_handler_factory(self) -> GetAgentConfigExecutionByIdHandler:
        return GetAgentConfigExecutionByIdHandler(
            queries=self._infra.agent_config_execution_query_service
        )

    def get_agent_skill_execution_handler_factory(self) -> GetAgentSkillExecutionByIdHandler:
        return GetAgentSkillExecutionByIdHandler(
            queries=self._infra.agent_skill_execution_query_service
        )

    def get_session_state_handler_factory(self) -> GetSessionStateByIdHandler:
        return GetSessionStateByIdHandler(queries=self._infra.session_state_query_service)


__all__ = ["Queries"]
