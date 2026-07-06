from __future__ import annotations

from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace używany w sygnaturze run() w runtime
)
from typing import TYPE_CHECKING, Any

from shell.bootstrap.execution.cli.command.command import RunnableCommand
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory

if TYPE_CHECKING:
    from shell.infrastructure.platform.configuration.shell_config import ShellConfig


class SmokeCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        config: ShellConfig = args.shell_config
        print(f"[smoke] using database: {config.database_url}")
        core_container = await ApplicationFactory(config).build()

        # Wyciągamy kontekst aplikacji do Any, uciszając mypy tylko raz
        app_ctx: Any = core_container.app

        app_ctx.buses.query_bus()

        print("[smoke] smoke command runs in reduced mode (import/start commands removed)")
        print("[smoke] OK")
