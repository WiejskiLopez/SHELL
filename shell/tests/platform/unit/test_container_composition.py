from __future__ import annotations

from shell.platform.bootstrap.container import Container, CoreContainer, Queries
from shell.platform.bootstrap.container.command_factories import Commands


def test_core_container_exports_preserve_public_api() -> None:
    assert Container is CoreContainer

    container = Container(db_url="sqlite+aiosqlite:///:memory:")

    assert isinstance(container.app.commands, Commands)
    assert isinstance(container.app.queries, Queries)
    assert container.app.buses.command_bus is not container.app.buses.query_bus


def test_handler_factories_create_transient_handlers() -> None:
    container = Container(db_url="sqlite+aiosqlite:///:memory:")

    first = container.app.commands.create_user_handler_factory()
    second = container.app.commands.create_user_handler_factory()

    assert type(first) is type(second)
    assert first is not second


def test_infrastructure_exposes_named_lifecycle_factories() -> None:
    container = Container(db_url="sqlite+aiosqlite:///:memory:")

    assert container.infra.clock_factory() is not container.infra.clock_factory()
    assert container.infra.id_generator_factory() is not container.infra.id_generator_factory()
    assert container.infra.unit_of_work_factory() is not container.infra.unit_of_work_factory()
