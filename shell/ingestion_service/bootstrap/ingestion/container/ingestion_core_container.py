from __future__ import annotations

from dependency_injector import containers, providers

from shell.ingestion_service.application.ingestion.ingestion.command_handlers.create_ingestion_handler import (
    CreateIngestionHandler,
)
from shell.ingestion_service.application.ingestion.ingestion.command_handlers.delete_ingestion_handler import (
    DeleteIngestionHandler,
)
from shell.ingestion_service.application.ingestion.ingestion.command_handlers.update_ingestion_handler import (
    UpdateIngestionHandler,
)
from shell.ingestion_service.application.ingestion.ingestion.commands.create_ingestion_command import (
    CreateIngestionCommand,
)
from shell.ingestion_service.application.ingestion.ingestion.commands.delete_ingestion_command import (
    DeleteIngestionCommand,
)
from shell.ingestion_service.application.ingestion.ingestion.commands.update_ingestion_command import (
    UpdateIngestionCommand,
)
from shell.ingestion_service.application.ingestion.ingestion.queries.get_ingestion_by_id_query import (
    GetIngestionByIdQuery,
)
from shell.ingestion_service.application.ingestion.ingestion.query_handlers.get_ingestion_by_id_handler import (
    GetIngestionByIdHandler,
)
from shell.ingestion_service.bootstrap.ingestion.contract_catalog import INGESTION_CONTRACT_CATALOG
from shell.ingestion_service.bootstrap.ingestion.event_registry import (
    build_ingestion_event_registry,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.repositories.ingestion_repository import (
    IngestionRepository,
)
from shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.ingestion_service.infrastructure.ingestion.persistence.sql.repositories.sql_ingestion_repository import (
    SqlIngestionRepository,
)
from shell.ingestion_service.infrastructure.ingestion.persistence.sql.services.ingestion_query_service import (
    IngestionQueryService,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.health.sql_readiness_probe import SqlReadinessProbe
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
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
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase
from shell.platform.infrastructure.serialization.command_registry import (
    build_command_registry,
    discover_command_types,
)
from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster
from shell.platform.infrastructure.time.system_clock import SystemClock


class IngestionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def _build_repo_map(self) -> dict[type, type]:
        return {IngestionRepository: SqlIngestionRepository}


class IngestionCoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    command_bus = providers.Singleton(CommandBus)
    persistence_delivery_models = providers.Object(PERSISTENCE_DELIVERY_MODELS)
    event_bus = providers.Singleton(EventBus)
    event_registry = providers.Singleton(build_ingestion_event_registry)
    event_inbox_processor_factory = providers.Factory(
        EventInboxProcessor,
        session_factory=session_factory,
        event_bus=event_bus,
        models=persistence_delivery_models.provided.events,
        registry=event_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="ingestion",
        worker_id=config.worker_id,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        envelope_policy=envelope_policy_from_catalog(INGESTION_CONTRACT_CATALOG),
        upcaster=providers.Singleton(PayloadUpcaster),
    )
    command_registry = providers.Object(
        build_command_registry(
            discover_command_types("shell.ingestion_service.application.ingestion")
        )
    )
    command_inbox_processor_factory = providers.Factory(
        CommandInboxProcessor,
        session_factory=session_factory,
        command_bus=command_bus,
        models=persistence_delivery_models.provided.commands,
        registry=command_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="ingestion-command",
        worker_id=config.command_worker_id,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        upcaster=providers.Singleton(PayloadUpcaster),
    )
    rabbit_command_inbox_consumer_factory = providers.Factory(
        RabbitInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.commands,
        queue_name="shell-ingestion-command-inbox",
        routing_keys=["command.#"],
    )
    rabbit_inbox_consumer_factory = providers.Factory(
        RabbitInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.events,
        queue_name="shell-ingestion-event-inbox",
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
    unit_of_work_factory = providers.Factory(
        IngestionUnitOfWork,
        session_factory=session_factory,
        models=persistence_delivery_models,
    )
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    query_bus = providers.Singleton(QueryBus)
    ingestion_query_service = providers.Singleton(
        IngestionQueryService, session_factory=session_factory
    )
    create_ingestion_handler_factory = providers.Factory(
        CreateIngestionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    update_ingestion_handler_factory = providers.Factory(
        UpdateIngestionHandler, unit_of_work=unit_of_work_factory, clock=clock_factory
    )
    delete_ingestion_handler_factory = providers.Factory(
        DeleteIngestionHandler, unit_of_work=unit_of_work_factory, clock=clock_factory
    )
    get_ingestion_by_id_handler_factory = providers.Factory(
        GetIngestionByIdHandler, queries=ingestion_query_service
    )


def configure_ingestion_container(container: IngestionCoreContainer) -> None:
    container.command_bus().register(
        CreateIngestionCommand, container.create_ingestion_handler_factory
    )
    container.command_bus().register(
        UpdateIngestionCommand, container.update_ingestion_handler_factory
    )
    container.command_bus().register(
        DeleteIngestionCommand, container.delete_ingestion_handler_factory
    )
    container.query_bus().register(
        GetIngestionByIdQuery, container.get_ingestion_by_id_handler_factory
    )
