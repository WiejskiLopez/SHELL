from __future__ import annotations

from dependency_injector import containers, providers

from shell.messaging.application.messaging.message_router.command_handlers.create_message_router_handler import (
    CreateMessageRouterHandler,
)
from shell.messaging.application.messaging.message_router.command_handlers.delete_message_router_handler import (
    DeleteMessageRouterHandler,
)
from shell.messaging.application.messaging.message_router.command_handlers.update_message_router_handler import (
    UpdateMessageRouterHandler,
)
from shell.messaging.application.messaging.message_router.commands.create_message_router_command import (
    CreateMessageRouterCommand,
)
from shell.messaging.application.messaging.message_router.commands.delete_message_router_command import (
    DeleteMessageRouterCommand,
)
from shell.messaging.application.messaging.message_router.commands.update_message_router_command import (
    UpdateMessageRouterCommand,
)
from shell.messaging.application.messaging.message_router.queries.get_message_by_id_query import (
    GetMessageByIdQuery,
)
from shell.messaging.application.messaging.message_router.query_handlers.get_message_by_id_handler import (
    GetMessageByIdHandler,
)
from shell.messaging.domain.messaging.aggregates.message_router.repositories.message_router_repository import (
    MessageRouterRepository,
)
from shell.messaging.infrastructure.messaging.persistence.sql.repositories.sql_message_router_repository import (
    SqlMessageRouterRepository,
)
from shell.messaging.infrastructure.messaging.persistence.sql.services.message_router_query_service import (
    MessageRouterQueryService,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase
from shell.platform.infrastructure.time.system_clock import SystemClock


class MessagingUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def _build_repo_map(self) -> dict[type, type]:
        return {MessageRouterRepository: SqlMessageRouterRepository}


class MessagingCoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    unit_of_work_factory = providers.Factory(MessagingUnitOfWork, session_factory=session_factory)
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    message_router_query_service = providers.Singleton(MessageRouterQueryService, session_factory=session_factory)
    create_message_router_handler_factory = providers.Factory(CreateMessageRouterHandler, unit_of_work=unit_of_work_factory, clock=clock_factory, id_generator=id_generator_factory)
    update_message_router_handler_factory = providers.Factory(UpdateMessageRouterHandler, unit_of_work=unit_of_work_factory, clock=clock_factory)
    delete_message_router_handler_factory = providers.Factory(DeleteMessageRouterHandler, unit_of_work=unit_of_work_factory, clock=clock_factory)
    get_message_by_id_handler_factory = providers.Factory(GetMessageByIdHandler, queries=message_router_query_service)


def configure_messaging_container(container: MessagingCoreContainer) -> None:
    container.command_bus().register(CreateMessageRouterCommand, container.create_message_router_handler_factory)
    container.command_bus().register(UpdateMessageRouterCommand, container.update_message_router_handler_factory)
    container.command_bus().register(DeleteMessageRouterCommand, container.delete_message_router_handler_factory)
    container.query_bus().register(GetMessageByIdQuery, container.get_message_by_id_handler_factory)
