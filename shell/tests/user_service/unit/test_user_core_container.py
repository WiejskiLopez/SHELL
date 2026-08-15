from __future__ import annotations

from shell.user_service.application.user.auth_session.commands.login_auth_session_command import (
    LoginAuthSessionCommand,
)
from shell.user_service.application.user.auth_session.commands.logout_auth_session_command import (
    LogoutAuthSessionCommand,
)
from shell.user_service.application.user.auth_session.queries.get_current_auth_session_query import (
    GetCurrentAuthSessionQuery,
)
from shell.user_service.application.user.user.commands.change_user_command import ChangeUserCommand
from shell.user_service.application.user.user.commands.create_user_command import CreateUserCommand
from shell.user_service.application.user.user.commands.delete_user_command import DeleteUserCommand
from shell.user_service.application.user.user.queries.get_user_by_email_query import (
    GetUserByEmailQuery,
)
from shell.user_service.application.user.user.queries.get_user_by_id_query import GetUserByIdQuery
from shell.user_service.application.user.user.queries.list_users_query import ListUsersQuery
from shell.user_service.application.user.user_skill.queries.get_user_skill_by_id_query import (
    GetUserSkillByIdQuery,
)
from shell.user_service.application.user.user_state.queries.get_user_state_by_id_query import (
    GetUserStateByIdQuery,
)
from shell.user_service.bootstrap.user.container.user_core_container import (
    UserCoreContainer,
    configure_user_container,
)


def test_user_core_container_registers_only_user_handlers() -> None:
    container = UserCoreContainer()
    container.config.db_url.from_value("sqlite+aiosqlite:///:memory:")

    configure_user_container(container)

    assert set(container.command_bus()._handler_factories) == {
        CreateUserCommand,
        ChangeUserCommand,
        DeleteUserCommand,
        LoginAuthSessionCommand,
        LogoutAuthSessionCommand,
    }
    assert set(container.query_bus()._factories) == {
        GetUserByIdQuery,
        GetUserByEmailQuery,
        ListUsersQuery,
        GetCurrentAuthSessionQuery,
        GetUserSkillByIdQuery,
        GetUserStateByIdQuery,
    }
    assert type(container.create_user_handler_factory()).__name__ == "CreateUserHandler"
