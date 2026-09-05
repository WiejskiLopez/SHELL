"""DefinitionCoreContainer — minimal DI container for the Definition BC microservice."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.definition_service.application.definition.graph_definition.queries.get_graph_definition_by_id_query import (
    GetGraphDefinitionByIdQuery,
)
from shell.definition_service.application.definition.graph_definition.queries.get_graph_definition_by_semantic_query import (
    GetGraphDefinitionBySemanticQuery,
)
from shell.definition_service.application.definition.graph_definition.query_handlers.get_graph_definition_by_id_handler import (
    GetGraphDefinitionByIdHandler,
)
from shell.definition_service.application.definition.graph_definition.query_handlers.get_graph_definition_by_semantic_handler import (
    GetGraphDefinitionBySemanticHandler,
)
from shell.definition_service.application.definition.node_definition.queries.get_node_definition_by_id_query import (
    GetNodeDefinitionByIdQuery,
)
from shell.definition_service.application.definition.node_definition.query_handlers.get_node_definition_by_id_handler import (
    GetNodeDefinitionByIdHandler,
)
from shell.definition_service.application.definition.runner_config.queries.get_runner_config_by_id_query import (
    GetRunnerConfigByIdQuery,
)
from shell.definition_service.application.definition.runner_config.query_handlers.get_runner_config_by_id_handler import (
    GetRunnerConfigByIdHandler,
)
from shell.definition_service.bootstrap.definition.contract_catalog import (
    DEFINITION_CONTRACT_CATALOG,
)
from shell.definition_service.bootstrap.definition.delivery import build_delivery_config
from shell.definition_service.bootstrap.definition.event_registry import (
    build_definition_event_registry,
)
from shell.definition_service.infrastructure.definition.graph_definition.persistence.sql.services.graph_definition_query_service import (
    SqlGraphDefinitionQueryService,
)
from shell.definition_service.infrastructure.definition.node_definition.persistence.sql.services.node_definition_query_service import (
    NodeDefinitionQueryService,
)
from shell.definition_service.infrastructure.definition.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.definition_service.infrastructure.definition.runner_config.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.messaging.event import EventInboxConsumer
from shell.platform.infrastructure.messaging.event.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
    envelope_policy_from_catalog,
)
from shell.platform.infrastructure.messaging.inbox.inbox_metrics_service import (
    InboxMetricsService,
)
from shell.platform.infrastructure.messaging.outbox.outbox_metrics_service import (
    OutboxMetricsService,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.platform.observability.infrastructure.health.composite_readiness_probe import (
    CompositeReadinessProbe,
)
from shell.platform.observability.infrastructure.health.rabbit_readiness_probe import (
    RabbitReadinessProbe,
)
from shell.platform.observability.infrastructure.health.sql_readiness_probe import SqlReadinessProbe
from shell.platform.observability.infrastructure.metrics.prometheus_metrics_backend import (
    PrometheusMetricsBackend,
)
from shell.platform.observability.infrastructure.metrics.registry import MetricsRegistry


class DefinitionCoreContainer(containers.DeclarativeContainer):
    """Minimal container for BC Definition — used when starting the definition microservice."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    persistence_delivery_models = providers.Object(PERSISTENCE_DELIVERY_MODELS)

    event_bus = providers.Singleton(EventBus)
    event_registry = providers.Singleton(build_definition_event_registry)
    event_inbox_processor_factory = providers.Factory(
        EventInboxProcessor,
        session_factory=session_factory,
        event_bus=event_bus,
        models=persistence_delivery_models.provided.events,
        registry=event_registry,
        worker_id=config.worker_id,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        envelope_policy=envelope_policy_from_catalog(DEFINITION_CONTRACT_CATALOG),
        upcaster=providers.Singleton(PayloadUpcaster),
    )
    rabbit_inbox_consumer_factory = providers.Factory(
        EventInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.events,
        queue_name="shell-definition-event-inbox",
    )

    metrics_exporter = providers.Singleton(MetricsRegistry)
    metrics_backend = providers.Singleton(PrometheusMetricsBackend, registry=metrics_exporter)
    inbox_metrics_service = providers.Singleton(
        InboxMetricsService,
        session_factory=session_factory,
        inbox_model=persistence_delivery_models.provided.events.inbox,
        backend=metrics_backend,
    )
    outbox_metrics_service = providers.Singleton(
        OutboxMetricsService,
        session_factory=session_factory,
        outbox_model=persistence_delivery_models.provided.events.outbox,
        backend=metrics_backend,
    )

    readiness_probe = providers.Singleton(
        CompositeReadinessProbe,
        probes=providers.List(
            providers.Singleton(
                SqlReadinessProbe,
                session_factory=session_factory,
                inbox_model=persistence_delivery_models.provided.events.inbox,
                max_backlog=1000,
                worker_heartbeat_model=persistence_delivery_models.provided.worker_heartbeat,
            ),
            providers.Singleton(
                RabbitReadinessProbe,
                url_provider=providers.Object(config.broker_url),
            ),
        ),
    )

    # Shared tools
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.definition_service")

    # Query services (read-only, bez UoW)
    graph_definition_query_service = providers.Singleton(
        SqlGraphDefinitionQueryService,
        session_factory=session_factory,
    )
    node_definition_query_service = providers.Singleton(
        NodeDefinitionQueryService, session_factory=session_factory
    )
    runner_config_query_service = providers.Singleton(
        RunnerConfigQueryService, session_factory=session_factory
    )

    get_graph_definition_by_id_handler_factory = providers.Factory(
        GetGraphDefinitionByIdHandler, queries=graph_definition_query_service
    )
    get_graph_definition_by_semantic_handler_factory = providers.Factory(
        GetGraphDefinitionBySemanticHandler, queries=graph_definition_query_service
    )
    get_node_definition_by_id_handler_factory = providers.Factory(
        GetNodeDefinitionByIdHandler, queries=node_definition_query_service
    )
    get_runner_config_by_id_handler_factory = providers.Factory(
        GetRunnerConfigByIdHandler, queries=runner_config_query_service
    )

    # Application buses
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    delivery_config = providers.Singleton(
        build_delivery_config,
        models=persistence_delivery_models,
        event_registry=event_registry,
        command_registry=None,
        event_bus=event_bus,
        command_bus=command_bus,
        event_transport=None,
        command_transport=None,
        session_factory=session_factory,
    )


def configure_definition_container(container: DefinitionCoreContainer) -> None:
    """Register Definition BC queries on the QueryBus."""
    query_bus = container.query_bus()
    query_bus.register(
        GetGraphDefinitionByIdQuery, container.get_graph_definition_by_id_handler_factory
    )
    query_bus.register(
        GetGraphDefinitionBySemanticQuery,
        container.get_graph_definition_by_semantic_handler_factory,
    )
    query_bus.register(
        GetNodeDefinitionByIdQuery, container.get_node_definition_by_id_handler_factory
    )
    query_bus.register(GetRunnerConfigByIdQuery, container.get_runner_config_by_id_handler_factory)
