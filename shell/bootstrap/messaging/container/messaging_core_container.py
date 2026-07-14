"""MessagingCoreContainer - minimal DI container for the standalone Messaging BC microservice."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.messaging.message_router.query_handlers.get_message_by_id_handler import (
    GetMessageByIdHandler,
)
from shell.infrastructure.messaging.persistence.sql.services.message_router_query_service import (
    MessageRouterQueryService,
)
from shell.platform.application.bus.message_bus import MessageBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock


class MessagingCoreContainer(containers.DeclarativeContainer):
    """Minimal container for BC Messaging — used when starting the messaging microservice."""

    config = providers.Configuration()

    # Database
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Query service
    message_router_query_service = providers.Singleton(
        MessageRouterQueryService, session_factory=session_factory
    )

    # Query handler
    get_message_handler_factory = providers.Factory(
        GetMessageByIdHandler, queries=message_router_query_service
    )

    # Shared tools
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.messaging")

    # Application buses
    message_bus = providers.Singleton(MessageBus)
