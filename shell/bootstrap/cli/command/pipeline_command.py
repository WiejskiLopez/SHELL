"""One-shot pipeline command: runs relay → processor once."""
from __future__ import annotations


from argparse import Namespace

from shell.bootstrap.cli.command.command import RunnableCommand
from shell.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell.bootstrap.factory.application_factory import ApplicationFactory


class PipelineCommand(RunnableCommand):
    """Runs full outbox → inbox → eventbus pipeline once."""

    async def run(self, args: Namespace) -> None:
        await bootstrap_database(args.db_url)
        core_container = await ApplicationFactory(database_url=args.db_url).build()

        relay = core_container.messaging.outbox_relay()
        processor = core_container.messaging.inbox_processor()

        outbox_count = await relay.run_once()
        inbox_count = await processor.run_once()

        print(f"[pipeline] outbox relay: {outbox_count} events")
        print(f"[pipeline] inbox processor: {inbox_count} events")
