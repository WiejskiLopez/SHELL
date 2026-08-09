"""Infrastructure dependencies used by the application container."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
from shell.infrastructure.execution.edge_execution.persistence.sql.unit_of_work import (
    SqlAlchemyEdgeExecutionUnitOfWork,
)
from shell.infrastructure.execution.edge_link_execution.persistence.sql.services.edge_link_execution_query_service import (
    EdgeLinkExecutionQueryService,
)
from shell.infrastructure.execution.edge_link_execution.persistence.sql.unit_of_work import (
    SqlAlchemyEdgeLinkExecutionUnitOfWork,
)
from shell.infrastructure.execution.node_execution.persistence.sql.services.node_result_query_service import (
    NodeResultQueryService,
)
from shell.infrastructure.execution.node_execution.persistence.sql.unit_of_work import (
    SqlAlchemyNodeExecutionUnitOfWork,
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
from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.unit_of_work import (
    SqlAlchemySchedulerDefinitionUnitOfWork,
)
from shell.infrastructure.scheduling.scheduler_execution.persistence.sql.services.scheduler_execution_query_service import (
    SchedulerExecutionQueryService,
)
from shell.infrastructure.scheduling.scheduler_job.persistence.sql.services.scheduler_job_query_service import (
    SchedulerJobQueryService,
)
from shell.infrastructure.session.session.persistence.sql.services.session_query_service import (
    SessionQueryService,
)
from shell.infrastructure.session.session_state.persistence.sql.services.session_state_query_service import (
    SessionStateQueryService,
)
from shell.infrastructure.user.auth_session.persistence.sql.services.auth_session_query_service import (
    AuthSessionQueryService,
)
from shell.infrastructure.user.auth_session.services.secure_token_generator import (
    SecureTokenGenerator,
)
from shell.infrastructure.user.auth_session.services.user_query_provider import SqlUserQueryProvider
from shell.infrastructure.user.user.persistence.sql.services.user_query_service import (
    UserQueryService,
)
from shell.infrastructure.user.user_skill.persistence.sql.services.user_skill_query_service import (
    UserSkillQueryService,
)
from shell.infrastructure.user.user_state.persistence.sql.services.user_state_query_service import (
    UserStateQueryService,
)
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
from shell.platform.infrastructure.messaging.message.sql_message_outbox_publisher import (
    SqlMessageOutboxPublisher,
)
from shell.platform.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock


class Infrastructure:
    """Container for infrastructure adapters and shared services."""

    def __init__(self, db_url: str) -> None:
        self.session_factory: async_sessionmaker[AsyncSession] = build_session_factory(db_url)
        self.unit_of_work_factory = self.create_unit_of_work
        self.node_execution_unit_of_work_factory = self.create_node_execution_unit_of_work
        self.edge_execution_unit_of_work_factory = self.create_edge_execution_unit_of_work
        self.edge_link_execution_unit_of_work_factory = (
            self.create_edge_link_execution_unit_of_work
        )
        self.scheduler_definition_unit_of_work_factory = (
            self.create_scheduler_definition_unit_of_work
        )

        self.task_execution_query_service = TaskExecutionQueryService(self.session_factory)
        self.workflow_query_service = WorkflowQueryService(self.session_factory)
        self.workflow_state_query_service = WorkflowStateQueryService(self.session_factory)
        self.node_result_query_service = NodeResultQueryService(self.session_factory)
        self.runner_config_query_service = RunnerConfigQueryService(self.session_factory)
        self.session_query_service = SessionQueryService(self.session_factory)
        self.session_state_query_service = SessionStateQueryService(self.session_factory)
        self.graph_definition_query_service_factory = self.create_graph_definition_query_service
        self.node_definition_query_service = NodeDefinitionQueryService(self.session_factory)
        self.user_query_service = UserQueryService(self.session_factory)
        self.auth_session_query_service = AuthSessionQueryService(self.session_factory)
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

        self.stdlib_logger = StdlibLogger("shell")
        self.clock_factory = SystemClock
        self.id_generator_factory = UuidIdGenerator
        self.token_generator_factory = SecureTokenGenerator
        self.user_query_provider = SqlUserQueryProvider(self.user_query_service)
        self.task_execution_loader_factory = FileSystemTaskLoader

        self.sql_command_outbox_publisher = SqlCommandOutboxPublisher(self.session_factory)
        self.sql_message_outbox_publisher = SqlMessageOutboxPublisher(self.session_factory)
        self.logging_publisher = LoggingEventPublisher(self.stdlib_logger)
        self.sql_audit_publisher = SqlAuditPublisher(self.session_factory)

    def create_unit_of_work(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(
            session_factory=self.session_factory,
            mapper=ReflectiveIntegrationMapper(),
        )

    def create_node_execution_unit_of_work(self) -> SqlAlchemyNodeExecutionUnitOfWork:
        return SqlAlchemyNodeExecutionUnitOfWork(
            session_factory=self.session_factory,
            mapper=ReflectiveIntegrationMapper(),
        )

    def create_edge_execution_unit_of_work(self) -> SqlAlchemyEdgeExecutionUnitOfWork:
        return SqlAlchemyEdgeExecutionUnitOfWork(
            session_factory=self.session_factory,
            mapper=ReflectiveIntegrationMapper(),
        )

    def create_edge_link_execution_unit_of_work(self) -> SqlAlchemyEdgeLinkExecutionUnitOfWork:
        return SqlAlchemyEdgeLinkExecutionUnitOfWork(
            session_factory=self.session_factory,
            mapper=ReflectiveIntegrationMapper(),
        )

    def create_scheduler_definition_unit_of_work(
        self,
    ) -> SqlAlchemySchedulerDefinitionUnitOfWork:
        return SqlAlchemySchedulerDefinitionUnitOfWork(
            session_factory=self.session_factory,
            mapper=ReflectiveIntegrationMapper(),
        )

    def create_graph_definition_query_service(self) -> SqlGraphDefinitionQueryService:
        return SqlGraphDefinitionQueryService(self.session_factory)
