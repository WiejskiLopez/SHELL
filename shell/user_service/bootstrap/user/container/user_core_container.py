"""UserCoreContainer — minimal DI container for the standalone User BC microservice."""

from __future__ import annotations

from datetime import timedelta

from dependency_injector import containers, providers

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.health.sql_readiness_probe import SqlReadinessProbe
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.mapping.reflective_integration_mapper import (
    ReflectiveIntegrationMapper,
)
from shell.platform.infrastructure.messaging.command.processor.command_inbox_processor import (
    CommandInboxProcessor,
)
from shell.platform.infrastructure.messaging.inbox.inbox_metrics_service import (
    InboxMetricsService,
)
from shell.platform.infrastructure.messaging.transport import OutboxToTransportRelay
from shell.platform.infrastructure.messaging.transport.rabbit import (
    RabbitDeliveryTransport,
    RabbitInboxConsumer,
)
from shell.platform.infrastructure.metrics.logging_metrics_backend import (
    LoggingMetricsBackend,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.serialization.command_registry import (
    build_command_registry,
    discover_command_types,
)
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.user_service.application.user.auth_session.command_handlers.login_auth_session_handler import (
    LoginAuthSessionHandler,
)
from shell.user_service.application.user.auth_session.command_handlers.logout_auth_session_handler import (
    LogoutAuthSessionHandler,
)
from shell.user_service.application.user.auth_session.commands.login_auth_session_command import (
    LoginAuthSessionCommand,
)
from shell.user_service.application.user.auth_session.commands.logout_auth_session_command import (
    LogoutAuthSessionCommand,
)
from shell.user_service.application.user.auth_session.queries.get_current_auth_session_query import (
    GetCurrentAuthSessionQuery,
)
from shell.user_service.application.user.auth_session.query_handlers.get_current_auth_session_handler import (
    GetCurrentAuthSessionHandler,
)
from shell.user_service.application.user.user.command_handlers.change_user_handler import (
    ChangeUserHandler,
)
from shell.user_service.application.user.user.command_handlers.create_user_handler import (
    CreateUserHandler,
)
from shell.user_service.application.user.user.command_handlers.delete_user_handler import (
    DeleteUserHandler,
)
from shell.user_service.application.user.user.commands.change_user_command import ChangeUserCommand
from shell.user_service.application.user.user.commands.create_user_command import CreateUserCommand
from shell.user_service.application.user.user.commands.delete_user_command import DeleteUserCommand
from shell.user_service.application.user.user.queries.get_user_by_email_query import (
    GetUserByEmailQuery,
)
from shell.user_service.application.user.user.queries.get_user_by_id_query import GetUserByIdQuery
from shell.user_service.application.user.user.queries.list_users_query import ListUsersQuery
from shell.user_service.application.user.user.query_handlers.get_user_by_email_handler import (
    GetUserByEmailHandler,
)
from shell.user_service.application.user.user.query_handlers.get_user_by_id_handler import (
    GetUserByIdHandler,
)
from shell.user_service.application.user.user.query_handlers.list_users_handler import (
    ListUsersHandler,
)
from shell.user_service.application.user.user_skill.queries.get_user_skill_by_id_query import (
    GetUserSkillByIdQuery,
)
from shell.user_service.application.user.user_skill.query_handlers.get_user_skill_by_id_handler import (
    GetUserSkillByIdHandler,
)
from shell.user_service.application.user.user_state.queries.get_user_state_by_id_query import (
    GetUserStateByIdQuery,
)
from shell.user_service.application.user.user_state.query_handlers.get_user_state_by_id_handler import (
    GetUserStateByIdHandler,
)
from shell.user_service.infrastructure.user.auth_session.persistence.sql.services.auth_session_query_service import (
    AuthSessionQueryService,
)
from shell.user_service.infrastructure.user.auth_session.services.secure_token_generator import (
    SecureTokenGenerator,
)
from shell.user_service.infrastructure.user.auth_session.services.user_query_provider import (
    SqlUserQueryProvider,
)
from shell.user_service.infrastructure.user.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.user_service.infrastructure.user.user.persistence.sql.services.user_query_service import (
    UserQueryService,
)
from shell.user_service.infrastructure.user.user.persistence.sql.unit_of_work import (
    SqlAlchemyUserUnitOfWork,
)
from shell.user_service.infrastructure.user.user_skill.persistence.sql.services.user_skill_query_service import (
    UserSkillQueryService,
)
from shell.user_service.infrastructure.user.user_state.persistence.sql.services.user_state_query_service import (
    UserStateQueryService,
)


class UserCoreContainer(containers.DeclarativeContainer):
    """Minimal container for BC User — used when starting the user microservice."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Per-BC Unit of Work — zna TYLKO repozytoria BC User
    persistence_delivery_models = providers.Object(PERSISTENCE_DELIVERY_MODELS)
    inbox_metrics_service = providers.Singleton(
        InboxMetricsService,
        session_factory=session_factory,
        inbox_model=persistence_delivery_models.provided.events.inbox,
        backend=LoggingMetricsBackend(),
    )
    readiness_probe = providers.Singleton(
        SqlReadinessProbe,
        session_factory=session_factory,
        inbox_model=persistence_delivery_models.provided.events.inbox,
        max_backlog=1000,
        worker_heartbeat_model=persistence_delivery_models.provided.worker_heartbeat,
    )
    integration_mapper = providers.Singleton(ReflectiveIntegrationMapper)
    unit_of_work_factory = providers.Factory(
        SqlAlchemyUserUnitOfWork,
        session_factory=session_factory,
        mapper=integration_mapper,
        models=persistence_delivery_models,
    )

    # Shared tools
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.user_service")

    # Application buses
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    command_registry = providers.Object(
        build_command_registry(discover_command_types("shell.user_service.application.user"))
    )
    command_inbox_processor_factory = providers.Factory(
        CommandInboxProcessor,
        session_factory=session_factory,
        command_bus=command_bus,
        models=persistence_delivery_models.provided.commands,
        registry=command_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="user-command",
        worker_id=config.command_worker_id,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
    )

    # Event delivery to the broker (Faza 9): outbox → Rabbit.
    delivery_transport = providers.Factory(
        RabbitDeliveryTransport,
        url=config.broker_url,
    )
    outbox_to_transport_relay_factory = providers.Factory(
        OutboxToTransportRelay,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.events,
        transport=delivery_transport,
        kind="event",
    )
    rabbit_command_inbox_consumer_factory = providers.Factory(
        RabbitInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.commands,
        queue_name="shell-user-command-inbox",
        routing_keys=["command.#"],
    )

    # Command Handlers — tylko User BC
    create_user_handler_factory = providers.Factory(
        CreateUserHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    change_user_handler_factory = providers.Factory(
        ChangeUserHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    delete_user_handler_factory = providers.Factory(
        DeleteUserHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )

    user_query_service = providers.Singleton(
        UserQueryService,
        session_factory=session_factory,
    )
    get_user_by_id_handler_factory = providers.Factory(
        GetUserByIdHandler,
        queries=user_query_service,
    )
    get_user_by_email_handler_factory = providers.Factory(
        GetUserByEmailHandler,
        queries=user_query_service,
    )
    list_users_handler_factory = providers.Factory(
        ListUsersHandler,
        queries=user_query_service,
    )
    user_skill_query_service = providers.Singleton(
        UserSkillQueryService,
        session_factory=session_factory,
    )
    get_user_skill_by_id_handler_factory = providers.Factory(
        GetUserSkillByIdHandler,
        queries=user_skill_query_service,
    )
    user_state_query_service = providers.Singleton(
        UserStateQueryService,
        session_factory=session_factory,
    )
    get_user_state_by_id_handler_factory = providers.Factory(
        GetUserStateByIdHandler,
        queries=user_state_query_service,
    )

    auth_session_query_service = providers.Singleton(
        AuthSessionQueryService,
        session_factory=session_factory,
    )
    user_query_provider = providers.Singleton(
        SqlUserQueryProvider,
        queries=user_query_service,
    )
    token_generator_factory = providers.Factory(SecureTokenGenerator)
    login_auth_session_handler_factory = providers.Factory(
        LoginAuthSessionHandler,
        unit_of_work=unit_of_work_factory,
        user_query_provider=user_query_provider,
        clock=clock_factory,
        token_generator=token_generator_factory,
        id_generator=id_generator_factory,
        session_ttl=timedelta(hours=24),
    )
    logout_auth_session_handler_factory = providers.Factory(
        LogoutAuthSessionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    get_current_auth_session_handler_factory = providers.Factory(
        GetCurrentAuthSessionHandler,
        queries=auth_session_query_service,
        clock=clock_factory,
    )


def configure_user_container(container: UserCoreContainer) -> None:
    """Register User BC commands and queries on its local buses."""

    command_bus = container.command_bus()
    query_bus = container.query_bus()

    command_bus.register(CreateUserCommand, container.create_user_handler_factory)
    command_bus.register(ChangeUserCommand, container.change_user_handler_factory)
    command_bus.register(DeleteUserCommand, container.delete_user_handler_factory)
    command_bus.register(
        LoginAuthSessionCommand,
        container.login_auth_session_handler_factory,
    )
    command_bus.register(
        LogoutAuthSessionCommand,
        container.logout_auth_session_handler_factory,
    )

    query_bus.register(GetUserByIdQuery, container.get_user_by_id_handler_factory)
    query_bus.register(GetUserByEmailQuery, container.get_user_by_email_handler_factory)
    query_bus.register(ListUsersQuery, container.list_users_handler_factory)
    query_bus.register(GetUserSkillByIdQuery, container.get_user_skill_by_id_handler_factory)
    query_bus.register(GetUserStateByIdQuery, container.get_user_state_by_id_handler_factory)
    query_bus.register(
        GetCurrentAuthSessionQuery,
        container.get_current_auth_session_handler_factory,
    )
