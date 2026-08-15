"""SessionCoreContainer — minimal DI container for the standalone Session BC microservice."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
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
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
    envelope_policy_from_catalog,
)
from shell.platform.infrastructure.messaging.inbox.inbox_metrics_service import (
    InboxMetricsService,
)
from shell.platform.infrastructure.messaging.transport.rabbit import RabbitInboxConsumer
from shell.platform.infrastructure.metrics.logging_metrics_backend import (
    LoggingMetricsBackend,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.serialization.command_registry import (
    build_command_registry,
    discover_command_types,
)
from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.session_service.application.session.session.command_handlers.change_session_handler import (
    ChangeSessionHandler,
)
from shell.session_service.application.session.session.command_handlers.close_session_handler import (
    CloseSessionHandler,
)
from shell.session_service.application.session.session.command_handlers.delete_session_handler import (
    DeleteSessionHandler,
)
from shell.session_service.application.session.session.command_handlers.open_session_handler import (
    OpenSessionHandler,
)
from shell.session_service.application.session.session.commands.change_session_command import (
    ChangeSessionCommand,
)
from shell.session_service.application.session.session.commands.close_session_command import (
    CloseSessionCommand,
)
from shell.session_service.application.session.session.commands.delete_session_command import (
    DeleteSessionCommand,
)
from shell.session_service.application.session.session.commands.open_session_command import (
    OpenSessionCommand,
)
from shell.session_service.application.session.session.event_handlers.auth_session_created_event_handler import (
    AuthSessionCreatedEventHandler,
)
from shell.session_service.application.session.session.queries.get_session_by_id_query import (
    GetSessionByIdQuery,
)
from shell.session_service.application.session.session.queries.get_session_history_query import (
    GetSessionHistoryQuery,
)
from shell.session_service.application.session.session.queries.list_sessions_query import (
    ListSessionsQuery,
)
from shell.session_service.application.session.session.query_handlers.get_session_by_id_handler import (
    GetSessionByIdHandler,
)
from shell.session_service.application.session.session.query_handlers.get_session_history_handler import (
    GetSessionHistoryHandler,
)
from shell.session_service.application.session.session.query_handlers.list_sessions_handler import (
    ListSessionsHandler,
)
from shell.session_service.application.session.session_state.queries.get_session_state_by_id_query import (
    GetSessionStateByIdQuery,
)
from shell.session_service.application.session.session_state.query_handlers.get_session_state_by_id_handler import (
    GetSessionStateByIdHandler,
)
from shell.session_service.bootstrap.session.contract_catalog import SESSION_CONTRACT_CATALOG
from shell.session_service.bootstrap.session.event_registry import build_session_event_registry
from shell.session_service.infrastructure.session.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.session_service.infrastructure.session.session.persistence.sql.services.session_query_service import (
    SessionQueryService,
)
from shell.session_service.infrastructure.session.session.persistence.sql.unit_of_work import (
    SqlAlchemySessionUnitOfWork,
)
from shell.session_service.infrastructure.session.session_state.persistence.sql.services.session_state_query_service import (
    SessionStateQueryService,
)


class SessionCoreContainer(containers.DeclarativeContainer):
    """Minimal container for BC Session — used when starting the session microservice."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Per-BC Unit of Work — zna TYLKO repozytoria BC Session
    persistence_delivery_models = providers.Object(PERSISTENCE_DELIVERY_MODELS)
    integration_mapper = providers.Singleton(ReflectiveIntegrationMapper)
    unit_of_work_factory = providers.Factory(
        SqlAlchemySessionUnitOfWork,
        session_factory=session_factory,
        mapper=integration_mapper,
        models=persistence_delivery_models,
    )

    # Shared tools
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.session_service")

    # Application buses
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    event_bus = providers.Singleton(EventBus)
    event_registry = providers.Singleton(build_session_event_registry)

    event_inbox_processor_factory = providers.Factory(
        EventInboxProcessor,
        session_factory=session_factory,
        event_bus=event_bus,
        models=persistence_delivery_models.provided.events,
        registry=event_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="session",
        worker_id=config.worker_id,
        upcaster=providers.Singleton(PayloadUpcaster),
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        envelope_policy=envelope_policy_from_catalog(SESSION_CONTRACT_CATALOG),
    )
    command_registry = providers.Object(
        build_command_registry(discover_command_types("shell.session_service.application.session"))
    )
    command_inbox_processor_factory = providers.Factory(
        CommandInboxProcessor,
        session_factory=session_factory,
        command_bus=command_bus,
        models=persistence_delivery_models.provided.commands,
        registry=command_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="session-command",
        worker_id=config.command_worker_id,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        upcaster=providers.Singleton(PayloadUpcaster),
    )

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

    # Consume cross-BC events from the broker (Faza 9): Rabbit → local inbox.
    rabbit_inbox_consumer_factory = providers.Factory(
        RabbitInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.events,
        queue_name="shell-session-event-inbox",
        routing_keys=["event.AuthSessionCreatedIntegrationEvent"],
    )
    rabbit_command_inbox_consumer_factory = providers.Factory(
        RabbitInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.commands,
        queue_name="shell-session-command-inbox",
        routing_keys=["command.#"],
    )

    session_query_service = providers.Singleton(
        SessionQueryService,
        session_factory=session_factory,
    )
    session_state_query_service = providers.Singleton(
        SessionStateQueryService,
        session_factory=session_factory,
    )

    auth_session_created_event_handler_factory = providers.Factory(
        AuthSessionCreatedEventHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )

    open_session_handler_factory = providers.Factory(
        OpenSessionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    close_session_handler_factory = providers.Factory(
        CloseSessionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    change_session_handler_factory = providers.Factory(
        ChangeSessionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    delete_session_handler_factory = providers.Factory(
        DeleteSessionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    get_session_history_handler_factory = providers.Factory(
        GetSessionHistoryHandler,
        queries=session_query_service,
    )
    get_session_by_id_handler_factory = providers.Factory(
        GetSessionByIdHandler,
        queries=session_query_service,
    )
    get_session_state_by_id_handler_factory = providers.Factory(
        GetSessionStateByIdHandler,
        queries=session_state_query_service,
    )
    list_sessions_handler_factory = providers.Factory(
        ListSessionsHandler,
        queries=session_query_service,
    )


def configure_session_container(container: SessionCoreContainer) -> None:
    """Register Session BC commands, queries and event subscriptions."""

    command_bus = container.command_bus()
    query_bus = container.query_bus()
    event_bus = container.event_bus()

    command_bus.register(OpenSessionCommand, container.open_session_handler_factory)
    command_bus.register(CloseSessionCommand, container.close_session_handler_factory)
    command_bus.register(ChangeSessionCommand, container.change_session_handler_factory)
    command_bus.register(DeleteSessionCommand, container.delete_session_handler_factory)

    query_bus.register(GetSessionHistoryQuery, container.get_session_history_handler_factory)
    query_bus.register(GetSessionByIdQuery, container.get_session_by_id_handler_factory)
    query_bus.register(ListSessionsQuery, container.list_sessions_handler_factory)
    query_bus.register(GetSessionStateByIdQuery, container.get_session_state_by_id_handler_factory)

    from shell.user_service.application.user.auth_session.integration_events.auth_session_created_integration_event import (
        AuthSessionCreatedIntegrationEvent,
    )

    event_bus.subscribe(
        AuthSessionCreatedIntegrationEvent,
        container.auth_session_created_event_handler_factory,
    )
