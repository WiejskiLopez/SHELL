"""DefinitionCoreContainer — minimal DI container for the Definition BC microservice."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.definition.bootstrap.definition.contract_catalog import DEFINITION_CONTRACT_CATALOG
from shell.definition.bootstrap.definition.event_registry import (
    build_definition_event_registry,
)
from shell.definition.infrastructure.definition.graph_definition.persistence.sql.services.graph_definition_query_service import (
    SqlGraphDefinitionQueryService,
)
from shell.definition.infrastructure.definition.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.definition.infrastructure.definition.runner_config.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.health.sql_readiness_probe import SqlReadinessProbe
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
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
from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster
from shell.platform.infrastructure.time.system_clock import SystemClock


class DefinitionCoreContainer(containers.DeclarativeContainer):
    """Minimal container for BC Definition — used when starting the definition microservice."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    persistence_delivery_models = providers.Object(PERSISTENCE_DELIVERY_MODELS)

    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    event_bus = providers.Singleton(EventBus)
    event_registry = providers.Singleton(build_definition_event_registry)
    event_inbox_processor_factory = providers.Factory(
        EventInboxProcessor,
        session_factory=session_factory,
        event_bus=event_bus,
        models=persistence_delivery_models.provided.events,
        registry=event_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="definition",
        worker_id=config.worker_id,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        envelope_policy=envelope_policy_from_catalog(DEFINITION_CONTRACT_CATALOG),
        upcaster=providers.Singleton(PayloadUpcaster),
    )
    rabbit_inbox_consumer_factory = providers.Factory(
        RabbitInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.events,
        queue_name="shell-definition-event-inbox",
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

    # Shared tools
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.definition")

    # Query services (read-only, bez UoW)
    graph_definition_query_service = providers.Singleton(
        SqlGraphDefinitionQueryService,
        session_factory=session_factory,
    )
    runner_config_query_service = providers.Singleton(
        RunnerConfigQueryService, session_factory=session_factory
    )

    # Application buses
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
