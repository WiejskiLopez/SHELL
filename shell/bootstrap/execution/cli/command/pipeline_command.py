"""One-shot pipeline command: runs relay → processor once."""
from __future__ import annotations

from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace używany w sygnaturze run() w runtime
)
from typing import TYPE_CHECKING

from shell.bootstrap.execution.cli.command.command import RunnableCommand
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory

if TYPE_CHECKING:
    from shell.infrastructure.platform.configuration.shell_config import ShellConfig


class PipelineCommand(RunnableCommand):
    """Runs full outbox → inbox → eventbus pipeline once."""

    async def run(self, args: Namespace) -> None:
        config: ShellConfig = args.shell_config
        core_container = await ApplicationFactory(config).build()

        relay = core_container.events.outbox_to_inbox_relay()
        processor = core_container.events.inbox_processor()

        outbox_count = await relay.run_once()
        inbox_count = await processor.run_once()

        print(f"[pipeline] outbox relay: {outbox_count} events")
        print(f"[pipeline] inbox processor: {inbox_count} events")
