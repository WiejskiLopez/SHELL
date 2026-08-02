"""Root DI container — Pure DI, manually wires infrastructure, domain and application layers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

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
from shell.application.user.user.command_handlers.create_user_handler import CreateUserHandler
from shell.application.user.user.command_handlers.delete_user_handler import DeleteUserHandler
from shell.application.user.user.command_handlers.login_handler import LoginHandler
from shell.application.user.user.command_handlers.update_user_handler import UpdateUserHandler
from shell.application.user.user.query_handlers.get_user_by_email_handler import (
    GetUserByEmailHandler,
)
from shell.application.user.user.query_handlers.get_user_by_id_handler import GetUserByIdHandler
from shell.application.user.user.query_handlers.list_users_handler import (
    ListUsersHandler,
)
from shell.application.user.user_skill.query_handlers.get_user_skill_by_id_handler import (
    GetUserSkillByIdHandler,
)
from shell.infrastructure.definition.graph_definition.persistence.sql.services.graph_definition_query_service import (
    SqlGraphDefinitionQueryService,
)
from shell.infrastructure.definition.node_definition.persistence.sql.services.node_definition_query_service import (
    NodeDefinitionQueryService,
)
from shell.infrastructure.definition.runner_config.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService,
)
from shell.infrastructure.execution.agent_config_execution.persistence.sql.services.agent_config_execution_query_service import (
    AgentConfigExecutionQueryService,
)
from shell.infrastructure.execution.agent_execution.persistence.sql.services.agent_execution_query_service import (
    AgentExecutionQueryService,
)
from shell.infrastructure.execution.agent_skill_execution.persistence.sql.services.agent_skill_execution_query_service import (
    AgentSkillExecutionQueryService,
)
from shell.infrastructure.execution.edge_execution.persistence.sql.services.edge_execution_query_service import (
    EdgeExecutionQueryService,
)
from shell.infrastructure.execution.edge_link_execution.persistence.sql.services.edge_link_execution_query_service import (
    EdgeLinkExecutionQueryService,
)
from shell.infrastructure.execution.node_execution.persistence.sql.services.node_result_query_service import (
    NodeResultQueryService,
)
from shell.infrastructure.execution.task_execution.filesystem.task_execution_loader import (
    FileSystemTaskLoader,
)
from shell.infrastructure.execution.task_execution.persistence.sql.services.task_execution_query_service import (
    TaskExecutionQueryService,
)
from shell.infrastructure.execution.user_execution.persistence.sql.services.user_execution_query_service import (
    UserExecutionQueryService,
)
from shell.infrastructure.execution.workflow.persistence.sql.services.workflow_query_service import (
    WorkflowQueryService,
)
from shell.infrastructure.execution.workflow_state.persistence.sql.services.workflow_state_query_service import (
    WorkflowStateQueryService,
)
from shell.infrastructure.messaging.persistence.sql.services.message_router_query_service import (
    MessageRouterQueryService,
)
from shell.infrastructure.project.project.persistence.sql.services.project_query_service import (
    ProjectQueryService,
)
from shell.infrastructure.project.project_skill.persistence.sql.services.project_skill_query_service import (
    ProjectSkillQueryService,
)
from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.services.scheduler_definition_query_service import (
    SchedulerDefinitionQueryService,
)
from shell.infrastructure.scheduling.scheduler_execution.persistence.sql.services.scheduler_execution_query_service import (
    SchedulerExecutionQueryService,
)
from shell.infrastructure.scheduling.scheduler_job.persistence.sql.services.scheduler_job_query_service import (
    SchedulerJobQueryService,
)
from shell.infrastructure.scheduling.services.scheduler_service import SchedulerService
from shell.infrastructure.session.session.persistence.sql.services.session_query_service import (
    SessionQueryService,
)
from shell.infrastructure.session.session_state.persistence.sql.services.session_state_query_service import (
    SessionStateQueryService,
)
from shell.infrastructure.user.user.persistence.sql.services.user_query_service import (
    UserQueryService,
)
from shell.infrastructure.user.user_skill.persistence.sql.services.user_skill_query_service import (
    UserSkillQueryService,
)
from shell.infrastructure.user.user_state.persistence.sql.services.user_state_query_service import (
    UserStateQueryService,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
from shell.platform.application.bus.event_bus_publisher import EventBusPublisher
from shell.platform.application.bus.message_bus import MessageBus
from shell.platform.application.bus.message_bus_publisher import MessageBusPublisher
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell.platform.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.mapping.reflective_integration_mapper import (
    ReflectiveIntegrationMapper,
)
from shell.platform.infrastructure.messaging.command.sql_command_outbox_publisher import (
    SqlCommandOutboxPublisher,
)
from shell.platform.infrastructure.messaging.event.event_outbox_to_inbox_relay import (
    EventOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.message.message_outbox_to_inbox_relay import (
    MessageOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.message.processor.message_inbox_processor import (
    MessageInboxProcessor,
)
from shell.platform.infrastructure.messaging.message.sql_message_outbox_publisher import (
    SqlMessageOutboxPublisher,
)
from shell.platform.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.serialization.event_registry import build_event_registry
from shell.platform.infrastructure.serialization.message_registry import build_message_registry
from shell.platform.infrastructure.time.system_clock import SystemClock

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.application.definition.graph_definition.query_handlers.get_graph_definition_by_id_handler import (
        GetGraphDefinitionByIdHandler,
    )
    from shell.application.definition.node_definition.query_handlers.get_node_definition_by_id_handler import (
        GetNodeDefinitionByIdHandler,
    )
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
    from shell.application.execution.edge_link_execution.query_handlers.get_edge_link_execution_by_id_handler import (
        GetEdgeLinkExecutionByIdHandler,
    )
    from shell.application.execution.node_execution.command_handlers.create_node_execution_handler import (
        CreateNodeExecutionHandler,
    )
    from shell.application.execution.node_execution.command_handlers.delete_node_execution_handler import (
        DeleteNodeExecutionHandler,
    )
    from shell.application.execution.node_execution.query_handlers.get_node_execution_by_id_handler import (
        GetNodeExecutionByIdHandler,
    )
    from shell.application.execution.task_execution.query_handlers.get_task_execution_by_id_handler import (
        GetTaskExecutionByIdHandler,
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
    from shell.application.messaging.message_router.query_handlers.get_message_by_id_handler import (
        GetMessageByIdHandler,
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
    from shell.application.session.session.event_handlers.user_login_succeeded_handler import (
        UserLoginSucceededHandler,
    )
    from shell.application.user.user_state.query_handlers.get_user_state_by_id_handler import (
        GetUserStateByIdHandler,
    )

logger = logging.getLogger(__name__)


class Buses:
    """Container for application buses — singletons shared across the system."""

    def __init__(self) -> None:
        self.command_bus = CommandBus()
        self.query_bus = QueryBus()
        self.event_bus = EventBus()
        self.message_bus = MessageBus()


class Infrastructure:
    """Container for infrastructure adapters and shared services."""

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url

        # Database
        self.session_factory: async_sessionmaker[AsyncSession] = build_session_factory(db_url)

        # Unit of Work factory — new UoW per request
        self.unit_of_work_factory = lambda: SqlAlchemyUnitOfWork(
            session_factory=self.session_factory,
            mapper=ReflectiveIntegrationMapper(),
        )

        # Query services (stateless, safe to share)
        self.task_execution_query_service = TaskExecutionQueryService(self.session_factory)
        self.workflow_query_service = WorkflowQueryService(self.session_factory)
        self.workflow_state_query_service = WorkflowStateQueryService(self.session_factory)
        self.node_result_query_service = NodeResultQueryService(self.session_factory)
        self.runner_config_query_service = RunnerConfigQueryService(self.session_factory)
        self.session_query_service = SessionQueryService(self.session_factory)
        self.session_state_query_service = SessionStateQueryService(self.session_factory)
        self.graph_definition_query_service_factory = lambda: SqlGraphDefinitionQueryService(
            self.session_factory
        )
        self.node_definition_query_service = NodeDefinitionQueryService(self.session_factory)
        self.user_query_service = UserQueryService(self.session_factory)
        self.user_skill_query_service = UserSkillQueryService(self.session_factory)
        self.user_state_query_service = UserStateQueryService(self.session_factory)
        self.user_execution_query_service = UserExecutionQueryService(self.session_factory)
        self.agent_execution_query_service = AgentExecutionQueryService(self.session_factory)
        self.agent_config_execution_query_service = AgentConfigExecutionQueryService(
            self.session_factory
        )
        self.agent_skill_execution_query_service = AgentSkillExecutionQueryService(
            self.session_factory
        )
        self.edge_execution_query_service = EdgeExecutionQueryService(self.session_factory)
        self.edge_link_execution_query_service = EdgeLinkExecutionQueryService(self.session_factory)
        self.message_router_query_service = MessageRouterQueryService(self.session_factory)
        self.project_query_service = ProjectQueryService(self.session_factory)
        self.project_skill_query_service = ProjectSkillQueryService(self.session_factory)
        self.scheduler_definition_query_service = SchedulerDefinitionQueryService(
            self.session_factory
        )
        self.scheduler_job_query_service = SchedulerJobQueryService(self.session_factory)
        self.scheduler_execution_query_service = SchedulerExecutionQueryService(
            self.session_factory
        )

        # Shared tools
        self.stdlib_logger = StdlibLogger("shell")
        self.clock_factory = lambda: SystemClock()
        self.id_generator_factory = lambda: UuidIdGenerator()
        self.task_execution_loader_factory = lambda: FileSystemTaskLoader()

        # HTTP clients for cross-BC communication
        self._create_http_clients()

        # Outbox/inbox publishers
        self.sql_command_outbox_publisher = SqlCommandOutboxPublisher(self.session_factory)
        self.sql_message_outbox_publisher = SqlMessageOutboxPublisher(self.session_factory)

        # Event publishers
        self.logging_publisher = LoggingEventPublisher(self.stdlib_logger)
        self.sql_audit_publisher = SqlAuditPublisher(self.session_factory)

    def _create_http_clients(self) -> None:
        pass


class Commands:
    """Container for command handler factories."""

    def __init__(self, buses: Buses, infra: Infrastructure) -> None:
        self._buses = buses
        self._infra = infra

    def delete_node_execution_handler_factory(self) -> DeleteNodeExecutionHandler:
        from shell.application.execution.node_execution.command_handlers.delete_node_execution_handler import (
            DeleteNodeExecutionHandler,
        )

        return DeleteNodeExecutionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def create_node_execution_handler_factory(self) -> CreateNodeExecutionHandler:
        from shell.application.execution.node_execution.command_handlers.create_node_execution_handler import (
            CreateNodeExecutionHandler,
        )
        from shell.infrastructure.execution.node_execution.persistence.sql.unit_of_work import (
            SqlAlchemyNodeExecutionUnitOfWork,
        )

        return CreateNodeExecutionHandler(
            unit_of_work=SqlAlchemyNodeExecutionUnitOfWork(
                session_factory=self._infra.session_factory,
                mapper=ReflectiveIntegrationMapper(),
            ),
            identity=self._infra.id_generator_factory(),
            time=self._infra.clock_factory(),
        )

    def create_edge_execution_handler_factory(self) -> CreateEdgeExecutionHandler:
        from shell.application.execution.edge_execution.command_handlers.create_edge_execution_handler import (
            CreateEdgeExecutionHandler,
        )
        from shell.infrastructure.execution.edge_execution.persistence.sql.unit_of_work import (
            SqlAlchemyEdgeExecutionUnitOfWork,
        )

        return CreateEdgeExecutionHandler(
            unit_of_work=SqlAlchemyEdgeExecutionUnitOfWork(
                session_factory=self._infra.session_factory,
                mapper=ReflectiveIntegrationMapper(),
            ),
            identity=self._infra.id_generator_factory(),
            time=self._infra.clock_factory(),
        )

    def update_edge_execution_handler_factory(self) -> UpdateEdgeExecutionHandler:
        from shell.application.execution.edge_execution.command_handlers.update_edge_execution_handler import (
            UpdateEdgeExecutionHandler,
        )
        from shell.infrastructure.execution.edge_execution.persistence.sql.unit_of_work import (
            SqlAlchemyEdgeExecutionUnitOfWork,
        )

        return UpdateEdgeExecutionHandler(
            unit_of_work=SqlAlchemyEdgeExecutionUnitOfWork(
                session_factory=self._infra.session_factory,
                mapper=ReflectiveIntegrationMapper(),
            ),
            time=self._infra.clock_factory(),
            logger=self._infra.stdlib_logger,
        )

    def delete_edge_execution_handler_factory(self) -> DeleteEdgeExecutionHandler:
        from shell.application.execution.edge_execution.command_handlers.delete_edge_execution_handler import (
            DeleteEdgeExecutionHandler,
        )
        from shell.infrastructure.execution.edge_execution.persistence.sql.unit_of_work import (
            SqlAlchemyEdgeExecutionUnitOfWork,
        )

        return DeleteEdgeExecutionHandler(
            unit_of_work=SqlAlchemyEdgeExecutionUnitOfWork(
                session_factory=self._infra.session_factory,
                mapper=ReflectiveIntegrationMapper(),
            ),
            time=self._infra.clock_factory(),
            logger=self._infra.stdlib_logger,
        )

    def create_edge_link_execution_handler_factory(self) -> CreateEdgeLinkExecutionHandler:
        from shell.application.execution.edge_link_execution.command_handlers.create_edge_link_execution_handler import (
            CreateEdgeLinkExecutionHandler,
        )
        from shell.infrastructure.execution.edge_link_execution.persistence.sql.unit_of_work import (
            SqlAlchemyEdgeLinkExecutionUnitOfWork,
        )

        return CreateEdgeLinkExecutionHandler(
            unit_of_work=SqlAlchemyEdgeLinkExecutionUnitOfWork(
                session_factory=self._infra.session_factory,
                mapper=ReflectiveIntegrationMapper(),
            ),
            identity=self._infra.id_generator_factory(),
            time=self._infra.clock_factory(),
        )

    def delete_edge_link_execution_handler_factory(self) -> DeleteEdgeLinkExecutionHandler:
        from shell.application.execution.edge_link_execution.command_handlers.delete_edge_link_execution_handler import (
            DeleteEdgeLinkExecutionHandler,
        )
        from shell.infrastructure.execution.edge_link_execution.persistence.sql.unit_of_work import (
            SqlAlchemyEdgeLinkExecutionUnitOfWork,
        )

        return DeleteEdgeLinkExecutionHandler(
            unit_of_work=SqlAlchemyEdgeLinkExecutionUnitOfWork(
                session_factory=self._infra.session_factory,
                mapper=ReflectiveIntegrationMapper(),
            ),
            time=self._infra.clock_factory(),
            logger=self._infra.stdlib_logger,
        )

    def update_edge_link_execution_handler_factory(self) -> UpdateEdgeLinkExecutionHandler:
        from shell.application.execution.edge_link_execution.command_handlers.update_edge_link_execution_handler import (
            UpdateEdgeLinkExecutionHandler,
        )
        from shell.infrastructure.execution.edge_link_execution.persistence.sql.unit_of_work import (
            SqlAlchemyEdgeLinkExecutionUnitOfWork,
        )

        return UpdateEdgeLinkExecutionHandler(
            unit_of_work=SqlAlchemyEdgeLinkExecutionUnitOfWork(
                session_factory=self._infra.session_factory,
                mapper=ReflectiveIntegrationMapper(),
            ),
            time=self._infra.clock_factory(),
            logger=self._infra.stdlib_logger,
        )

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

    def login_handler_factory(self) -> LoginHandler:
        return LoginHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            queries=self._infra.user_query_service,
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
        from shell.application.scheduling.scheduler_definition.command_handlers.create_scheduler_definition_handler import (
            CreateSchedulerDefinitionHandler,
        )
        from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.unit_of_work import (
            SqlAlchemySchedulerDefinitionUnitOfWork,
        )

        return CreateSchedulerDefinitionHandler(
            unit_of_work=SqlAlchemySchedulerDefinitionUnitOfWork(
                session_factory=self._infra.session_factory,
                mapper=ReflectiveIntegrationMapper(),
            ),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def update_scheduler_definition_handler_factory(self) -> UpdateSchedulerDefinitionHandler:
        from shell.application.scheduling.scheduler_definition.command_handlers.update_scheduler_definition_handler import (
            UpdateSchedulerDefinitionHandler,
        )

        return UpdateSchedulerDefinitionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_scheduler_definition_handler_factory(self) -> DeleteSchedulerDefinitionHandler:
        from shell.application.scheduling.scheduler_definition.command_handlers.delete_scheduler_definition_handler import (
            DeleteSchedulerDefinitionHandler,
        )

        return DeleteSchedulerDefinitionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def create_scheduler_execution_handler_factory(self) -> CreateSchedulerExecutionHandler:
        from shell.application.scheduling.scheduler_execution.command_handlers.create_scheduler_execution_handler import (
            CreateSchedulerExecutionHandler,
        )

        return CreateSchedulerExecutionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def update_scheduler_execution_handler_factory(self) -> UpdateSchedulerExecutionHandler:
        from shell.application.scheduling.scheduler_execution.command_handlers.update_scheduler_execution_handler import (
            UpdateSchedulerExecutionHandler,
        )

        return UpdateSchedulerExecutionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_scheduler_execution_handler_factory(self) -> DeleteSchedulerExecutionHandler:
        from shell.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
            DeleteSchedulerExecutionHandler,
        )

        return DeleteSchedulerExecutionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def create_scheduler_job_handler_factory(self) -> CreateSchedulerJobHandler:
        from shell.application.scheduling.scheduler_job.command_handlers.create_scheduler_job_handler import (
            CreateSchedulerJobHandler,
        )

        return CreateSchedulerJobHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def update_scheduler_job_handler_factory(self) -> UpdateSchedulerJobHandler:
        from shell.application.scheduling.scheduler_job.command_handlers.update_scheduler_job_handler import (
            UpdateSchedulerJobHandler,
        )

        return UpdateSchedulerJobHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_scheduler_job_handler_factory(self) -> DeleteSchedulerJobHandler:
        from shell.application.scheduling.scheduler_job.command_handlers.delete_scheduler_job_handler import (
            DeleteSchedulerJobHandler,
        )

        return DeleteSchedulerJobHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

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


class EventHandlers:
    """Container for event handler factories."""

    def __init__(self, buses: Buses, infra: Infrastructure) -> None:
        self._buses = buses
        self._infra = infra

    def user_login_succeeded_handler_factory(self) -> UserLoginSucceededHandler:
        from shell.application.session.session.event_handlers.user_login_succeeded_handler import (
            UserLoginSucceededHandler,
        )
        from shell.domain.session.services.session_management_service import (
            SessionManagementService,
        )

        return UserLoginSucceededHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            session_service=SessionManagementService(
                id_generator=self._infra.id_generator_factory(),
            ),
        )


class Queries:
    """Container for query handler factories."""

    def __init__(self, infra: Infrastructure) -> None:
        self._infra = infra

    def get_graph_definition_handler_factory(self) -> GetGraphDefinitionByIdHandler:
        from shell.application.definition.graph_definition.query_handlers.get_graph_definition_by_id_handler import (
            GetGraphDefinitionByIdHandler,
        )

        return GetGraphDefinitionByIdHandler(
            queries=self._infra.graph_definition_query_service_factory()  # type: ignore[arg-type]
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
        return ListUsersHandler(queries=self._infra.user_query_service)

    def list_projects_handler_factory(self) -> ListProjectsHandler:
        return ListProjectsHandler(queries=self._infra.project_query_service)

    def list_task_executions_handler_factory(self) -> ListTaskExecutionsHandler:
        return ListTaskExecutionsHandler(queries=self._infra.task_execution_query_service)

    def get_workflow_state_handler_factory(self) -> GetWorkflowStateByIdHandler:
        return GetWorkflowStateByIdHandler(queries=self._infra.workflow_query_service)  # type: ignore[arg-type]

    def get_session_history_handler_factory(self) -> GetSessionHistoryHandler:
        return GetSessionHistoryHandler(queries=self._infra.session_query_service)

    def list_sessions_handler_factory(self) -> ListSessionsHandler:
        return ListSessionsHandler(queries=self._infra.session_query_service)

    def get_graph_execution_handler_factory(self) -> GetGraphExecutionByIdHandler:
        return GetGraphExecutionByIdHandler(
            queries=self._infra.graph_definition_query_service_factory()  # type: ignore[arg-type]
        )

    def get_user_handler_factory(self) -> GetUserByIdHandler:
        return GetUserByIdHandler(queries=self._infra.user_query_service)

    def get_user_by_email_handler_factory(self) -> GetUserByEmailHandler:
        return GetUserByEmailHandler(queries=self._infra.user_query_service)

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

        return GetMessageByIdHandler(queries=self._infra.message_router_query_service)  # type: ignore[arg-type]

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


class Application:
    """Container for application layer — buses, commands, queries, events."""

    def __init__(self, infra: Infrastructure) -> None:
        self.buses = Buses()
        self.commands = Commands(buses=self.buses, infra=infra)
        self.queries = Queries(infra=infra)
        self.event_handlers = EventHandlers(buses=self.buses, infra=infra)


class Events:
    """Container for event/command outbox/inbox infrastructure."""

    def __init__(
        self,
        infra: Infrastructure,
        buses: Buses,
        events_config: dict[str, Any] | None = None,
    ) -> None:
        ec = events_config or {}
        self._infra = infra
        self._buses = buses

        # Event registry for deserialization
        self._event_registry = build_event_registry()

        # Event publisher
        self._event_bus_publisher = EventBusPublisher(event_bus=buses.event_bus)

        # Message registry for deserialization
        self._message_registry = build_message_registry()

        # Message publisher
        self._message_bus_publisher = MessageBusPublisher(message_bus=buses.message_bus)

        self._outbox_batch_size = ec.get("outbox_batch_size", 100)
        self._inbox_batch_size = ec.get("inbox_batch_size", 50)
        self._command_outbox_batch_size = ec.get("command_outbox_batch_size", 100)
        self._command_inbox_batch_size = ec.get("command_inbox_batch_size", 50)

    def event_outbox_to_inbox_relay(self) -> EventOutboxToInboxRelay:
        return EventOutboxToInboxRelay(
            session_factory=self._infra.session_factory,
            downstream=self._event_bus_publisher,
            batch_size=self._outbox_batch_size,
        )

    def event_inbox_processor(self) -> EventInboxProcessor:
        return EventInboxProcessor(
            session_factory=self._infra.session_factory,
            event_bus=self._event_bus_publisher,
            batch_size=self._inbox_batch_size,
            registry=self._event_registry,
        )

    def message_outbox_to_inbox_relay(self) -> MessageOutboxToInboxRelay:
        return MessageOutboxToInboxRelay(
            session_factory=self._infra.session_factory,
            downstream=self._message_bus_publisher,
            batch_size=self._outbox_batch_size,
        )

    def message_inbox_processor(self) -> MessageInboxProcessor:
        return MessageInboxProcessor(
            session_factory=self._infra.session_factory,
            message_bus=self._message_bus_publisher,
            batch_size=self._inbox_batch_size,
            registry=self._message_registry,
        )


class Container:
    """Root Pure DI container — composes all layers of the system.

    Usage:
        container = Container(db_url="sqlite+aiosqlite:///shell.db")
        await container.buses.command_bus.dispatch(command)
        container.application.buses.query_bus.dispatch(query)
        relay = container.events.event_outbox_to_inbox_relay()
    """

    def __init__(
        self,
        db_url: str = "",
        events_config: dict[str, Any] | None = None,
    ) -> None:
        self._db_url = db_url
        self._events_config = events_config

        # Infrastructure
        self.infra = Infrastructure(db_url=db_url)

        # Application
        self.app = Application(infra=self.infra)

        # Events
        self.events = Events(
            infra=self.infra,
            buses=self.app.buses,
            events_config=events_config,
        )

        # Scheduler service
        self.scheduler_service = SchedulerService(
            session_factory=self.infra.session_factory,
            event_outbox_to_inbox_relay=self.events.event_outbox_to_inbox_relay,  # type: ignore[arg-type]
            event_inbox_processor=self.events.event_inbox_processor,  # type: ignore[arg-type]
            message_outbox_to_inbox_relay=self.events.message_outbox_to_inbox_relay,  # type: ignore[arg-type]
            message_inbox_processor=self.events.message_inbox_processor,  # type: ignore[arg-type]
        )


# Alias for backward compat
CoreContainer = Container
