"""UserCoreContainer — minimalny kontener DI dla samodzielnego mikroserwisu User BC."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.platform.bus.command_bus import CommandBus
from shell.application.platform.bus.query_bus import QueryBus
from shell.application.user.user.command_handlers.user_create_handler import UserCreateHandler
from shell.application.user.user.command_handlers.user_delete_handler import UserDeleteHandler
from shell.application.user.user.command_handlers.user_update_handler import UserUpdateHandler
from shell.infrastructure.platform.identity.uuid_id_generator import UuidIdGenerator
from shell.infrastructure.platform.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.platform.persistence.sql import build_session_factory
from shell.infrastructure.platform.time.system_clock import SystemClock
from shell.infrastructure.user.user.persistence.sql.unit_of_work import SqlAlchemyUserUnitOfWork


class UserCoreContainer(containers.DeclarativeContainer):
    """Minimalny kontener dla BC User — używany przy starcie mikroserwisu user."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Per-BC Unit of Work — zna TYLKO repozytoria BC User
    unit_of_work_factory = providers.Factory(
        SqlAlchemyUserUnitOfWork,
        session_factory=session_factory,
    )

    # Narzędzia wspólne
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.user")

    # Szyny aplikacyjne
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)

    # Command Handlers — tylko User BC
    create_user_handler_factory = providers.Factory(
        UserCreateHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    update_user_handler_factory = providers.Factory(
        UserUpdateHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    delete_user_handler_factory = providers.Factory(
        UserDeleteHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
