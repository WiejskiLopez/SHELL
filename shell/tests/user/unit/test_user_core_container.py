from __future__ import annotations

from shell.user.application.user.auth_session.commands.login_auth_session_command import (
    LoginAuthSessionCommand,
)
from shell.user.application.user.auth_session.commands.logout_auth_session_command import (
    LogoutAuthSessionCommand,
)
from shell.user.application.user.auth_session.queries.get_current_auth_session_query import (
    GetCurrentAuthSessionQuery,
)
from shell.user.application.user.user.commands.create_user_command import CreateUserCommand
from shell.user.application.user.user.commands.delete_user_command import DeleteUserCommand
from shell.user.application.user.user.commands.update_user_command import UpdateUserCommand
from shell.user.application.user.user.queries.get_user_by_email_query import GetUserByEmailQuery
from shell.user.application.user.user.queries.get_user_by_id_query import GetUserByIdQuery
from shell.user.application.user.user.queries.list_users_query import ListUsersQuery
from shell.user.bootstrap.user.container.user_core_container import (
    UserCoreContainer,
    configure_user_container,
)


def test_user_core_container_registers_only_user_handlers() -> None:
    container = UserCoreContainer()
    container.config.db_url.from_value("sqlite+aiosqlite:///:memory:")

    configure_user_container(container)

    assert set(container.command_bus()._handler_factories) == {
        CreateUserCommand,
        UpdateUserCommand,
        DeleteUserCommand,
        LoginAuthSessionCommand,
        LogoutAuthSessionCommand,
    }
    assert set(container.query_bus()._factories) == {
        GetUserByIdQuery,
        GetUserByEmailQuery,
        ListUsersQuery,
        GetCurrentAuthSessionQuery,
    }
    assert type(container.create_user_handler_factory()).__name__ == "CreateUserHandler"
