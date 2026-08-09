"""Pure-DI factories for application command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.user.user.command_handlers.create_user_handler import CreateUserHandler
from shell.application.user.user.command_handlers.delete_user_handler import DeleteUserHandler
from shell.application.user.user.command_handlers.update_user_handler import UpdateUserHandler
from shell.platform.bootstrap.container.execution_command_factories import (
    ExecutionCommandFactories,
)
from shell.platform.bootstrap.container.scheduling_command_factories import (
    SchedulingCommandFactories,
)

if TYPE_CHECKING:
    from shell.application.execution.edge_execution.command_handlers.create_edge_execution_handler import (
        CreateEdgeExecutionHandler,
    )
    from shell.application.execution.edge_execution.command_handlers.delete_edge_execution_handler import (
        DeleteEdgeExecutionHandler,
    )
    from shell.application.execution.edge_execution.command_handlers.update_edge_execution_handler import (
        UpdateEdgeExecutionHandler,
    )
    from shell.application.execution.edge_link_execution.command_handlers.create_edge_link_execution_handler import (
        CreateEdgeLinkExecutionHandler,
    )
    from shell.application.execution.edge_link_execution.command_handlers.delete_edge_link_execution_handler import (
        DeleteEdgeLinkExecutionHandler,
    )
    from shell.application.execution.edge_link_execution.command_handlers.update_edge_link_execution_handler import (
        UpdateEdgeLinkExecutionHandler,
    )
    from shell.application.execution.node_execution.command_handlers.create_node_execution_handler import (
        CreateNodeExecutionHandler,
    )
    from shell.application.execution.node_execution.command_handlers.delete_node_execution_handler import (
        DeleteNodeExecutionHandler,
    )
    from shell.application.execution.workflow.command_handlers.create_workflow_handler import (
        CreateWorkflowHandler,
    )
    from shell.application.execution.workflow.command_handlers.delete_workflow_handler import (
        DeleteWorkflowHandler,
    )
    from shell.application.execution.workflow.command_handlers.update_workflow_handler import (
        UpdateWorkflowHandler,
    )
    from shell.application.messaging.message_router.command_handlers.create_message_router_handler import (
        CreateMessageRouterHandler,
    )
    from shell.application.messaging.message_router.command_handlers.delete_message_router_handler import (
        DeleteMessageRouterHandler,
    )
    from shell.application.messaging.message_router.command_handlers.update_message_router_handler import (
        UpdateMessageRouterHandler,
    )
    from shell.application.project.project.command_handlers.create_project_handler import (
        CreateProjectHandler,
    )
    from shell.application.project.project.command_handlers.delete_project_handler import (
        DeleteProjectHandler,
    )
    from shell.application.project.project.command_handlers.update_project_handler import (
        UpdateProjectHandler,
    )
    from shell.application.scheduling.scheduler_definition.command_handlers.create_scheduler_definition_handler import (
        CreateSchedulerDefinitionHandler,
    )
    from shell.application.scheduling.scheduler_definition.command_handlers.delete_scheduler_definition_handler import (
        DeleteSchedulerDefinitionHandler,
    )
    from shell.application.scheduling.scheduler_definition.command_handlers.update_scheduler_definition_handler import (
        UpdateSchedulerDefinitionHandler,
    )
    from shell.application.scheduling.scheduler_execution.command_handlers.create_scheduler_execution_handler import (
        CreateSchedulerExecutionHandler,
    )
    from shell.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
        DeleteSchedulerExecutionHandler,
    )
    from shell.application.scheduling.scheduler_execution.command_handlers.update_scheduler_execution_handler import (
        UpdateSchedulerExecutionHandler,
    )
    from shell.application.scheduling.scheduler_job.command_handlers.create_scheduler_job_handler import (
        CreateSchedulerJobHandler,
    )
    from shell.application.scheduling.scheduler_job.command_handlers.delete_scheduler_job_handler import (
        DeleteSchedulerJobHandler,
    )
    from shell.application.scheduling.scheduler_job.command_handlers.update_scheduler_job_handler import (
        UpdateSchedulerJobHandler,
    )
    from shell.application.session.session.command_handlers.close_session_handler import (
        CloseSessionHandler,
    )
    from shell.application.session.session.command_handlers.delete_session_handler import (
        DeleteSessionHandler,
    )
    from shell.application.session.session.command_handlers.open_session_handler import (
        OpenSessionHandler,
    )
    from shell.application.session.session.command_handlers.update_session_handler import (
        UpdateSessionHandler,
    )
    from shell.application.user.auth_session.command_handlers.login_auth_session_handler import (
        LoginAuthSessionHandler,
    )
    from shell.application.user.auth_session.command_handlers.logout_auth_session_handler import (
        LogoutAuthSessionHandler,
    )
    from shell.application.user.auth_session.query_handlers.get_current_auth_session_handler import (
        GetCurrentAuthSessionHandler,
    )
    from shell.platform.bootstrap.container.infrastructure import Infrastructure
class Commands(ExecutionCommandFactories, SchedulingCommandFactories):
    """Container for command handler factories."""

    def __init__(self, infra: Infrastructure) -> None:
        self._infra = infra

    def delete_node_execution_handler_factory(self) -> DeleteNodeExecutionHandler:
        return super().delete_node_execution_handler_factory()

    def create_node_execution_handler_factory(self) -> CreateNodeExecutionHandler:
        return super().create_node_execution_handler_factory()

    def create_edge_execution_handler_factory(self) -> CreateEdgeExecutionHandler:
        return super().create_edge_execution_handler_factory()

    def update_edge_execution_handler_factory(self) -> UpdateEdgeExecutionHandler:
        return super().update_edge_execution_handler_factory()

    def delete_edge_execution_handler_factory(self) -> DeleteEdgeExecutionHandler:
        return super().delete_edge_execution_handler_factory()

    def create_edge_link_execution_handler_factory(self) -> CreateEdgeLinkExecutionHandler:
        return super().create_edge_link_execution_handler_factory()

    def delete_edge_link_execution_handler_factory(self) -> DeleteEdgeLinkExecutionHandler:
        return super().delete_edge_link_execution_handler_factory()

    def update_edge_link_execution_handler_factory(self) -> UpdateEdgeLinkExecutionHandler:
        return super().update_edge_link_execution_handler_factory()

    def create_user_handler_factory(self) -> CreateUserHandler:
        return CreateUserHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def update_user_handler_factory(self) -> UpdateUserHandler:
        return UpdateUserHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_user_handler_factory(self) -> DeleteUserHandler:
        return DeleteUserHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def login_auth_session_handler_factory(self) -> LoginAuthSessionHandler:
        from datetime import timedelta

        from shell.application.user.auth_session.command_handlers.login_auth_session_handler import (
            LoginAuthSessionHandler,
        )

        return LoginAuthSessionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            user_query_provider=self._infra.user_query_provider,
            clock=self._infra.clock_factory(),
            token_generator=self._infra.token_generator_factory(),
            id_generator=self._infra.id_generator_factory(),
            session_ttl=timedelta(hours=24),
        )

    def logout_auth_session_handler_factory(self) -> LogoutAuthSessionHandler:
        from shell.application.user.auth_session.command_handlers.logout_auth_session_handler import (
            LogoutAuthSessionHandler as RuntimeLogoutAuthSessionHandler,
        )

        return RuntimeLogoutAuthSessionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def get_current_auth_session_handler_factory(self) -> GetCurrentAuthSessionHandler:
        from shell.application.user.auth_session.query_handlers.get_current_auth_session_handler import (
            GetCurrentAuthSessionHandler as RuntimeGetCurrentAuthSessionHandler,
        )

        return RuntimeGetCurrentAuthSessionHandler(
            queries=self._infra.auth_session_query_service,
            clock=self._infra.clock_factory(),
        )

    def open_session_handler_factory(self) -> OpenSessionHandler:
        from shell.application.session.session.command_handlers.open_session_handler import (
            OpenSessionHandler,
        )

        return OpenSessionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def close_session_handler_factory(self) -> CloseSessionHandler:
        from shell.application.session.session.command_handlers.close_session_handler import (
            CloseSessionHandler,
        )

        return CloseSessionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def update_session_handler_factory(self) -> UpdateSessionHandler:
        from shell.application.session.session.command_handlers.update_session_handler import (
            UpdateSessionHandler,
        )

        return UpdateSessionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_session_handler_factory(self) -> DeleteSessionHandler:
        from shell.application.session.session.command_handlers.delete_session_handler import (
            DeleteSessionHandler,
        )

        return DeleteSessionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def create_scheduler_definition_handler_factory(self) -> CreateSchedulerDefinitionHandler:
        return super().create_scheduler_definition_handler_factory()

    def update_scheduler_definition_handler_factory(self) -> UpdateSchedulerDefinitionHandler:
        return super().update_scheduler_definition_handler_factory()

    def delete_scheduler_definition_handler_factory(self) -> DeleteSchedulerDefinitionHandler:
        return super().delete_scheduler_definition_handler_factory()

    def create_scheduler_execution_handler_factory(self) -> CreateSchedulerExecutionHandler:
        return super().create_scheduler_execution_handler_factory()

    def update_scheduler_execution_handler_factory(self) -> UpdateSchedulerExecutionHandler:
        return super().update_scheduler_execution_handler_factory()

    def delete_scheduler_execution_handler_factory(self) -> DeleteSchedulerExecutionHandler:
        return super().delete_scheduler_execution_handler_factory()

    def create_scheduler_job_handler_factory(self) -> CreateSchedulerJobHandler:
        return super().create_scheduler_job_handler_factory()

    def update_scheduler_job_handler_factory(self) -> UpdateSchedulerJobHandler:
        return super().update_scheduler_job_handler_factory()

    def delete_scheduler_job_handler_factory(self) -> DeleteSchedulerJobHandler:
        return super().delete_scheduler_job_handler_factory()

    def create_message_router_handler_factory(self) -> CreateMessageRouterHandler:
        from shell.application.messaging.message_router.command_handlers.create_message_router_handler import (
            CreateMessageRouterHandler,
        )

        return CreateMessageRouterHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def update_message_router_handler_factory(self) -> UpdateMessageRouterHandler:
        from shell.application.messaging.message_router.command_handlers.update_message_router_handler import (
            UpdateMessageRouterHandler,
        )

        return UpdateMessageRouterHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_message_router_handler_factory(self) -> DeleteMessageRouterHandler:
        from shell.application.messaging.message_router.command_handlers.delete_message_router_handler import (
            DeleteMessageRouterHandler,
        )

        return DeleteMessageRouterHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def create_project_handler_factory(self) -> CreateProjectHandler:
        from shell.application.project.project.command_handlers.create_project_handler import (
            CreateProjectHandler,
        )

        return CreateProjectHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def update_project_handler_factory(self) -> UpdateProjectHandler:
        from shell.application.project.project.command_handlers.update_project_handler import (
            UpdateProjectHandler,
        )

        return UpdateProjectHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_project_handler_factory(self) -> DeleteProjectHandler:
        from shell.application.project.project.command_handlers.delete_project_handler import (
            DeleteProjectHandler,
        )

        return DeleteProjectHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def create_workflow_handler_factory(self) -> CreateWorkflowHandler:
        from shell.application.execution.workflow.command_handlers.create_workflow_handler import (
            CreateWorkflowHandler,
        )

        return CreateWorkflowHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def update_workflow_handler_factory(self) -> UpdateWorkflowHandler:
        from shell.application.execution.workflow.command_handlers.update_workflow_handler import (
            UpdateWorkflowHandler,
        )

        return UpdateWorkflowHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_workflow_handler_factory(self) -> DeleteWorkflowHandler:
        from shell.application.execution.workflow.command_handlers.delete_workflow_handler import (
            DeleteWorkflowHandler,
        )

        return DeleteWorkflowHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )


__all__ = ["Commands"]

