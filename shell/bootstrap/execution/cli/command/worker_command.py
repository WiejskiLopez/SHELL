"""Production background scheduler command."""
from __future__ import annotations

import asyncio
from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace używany w sygnaturze run() w runtime
)

from shell.bootstrap.execution.cli.command.command import RunnableCommand
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory


class WorkerCommand(RunnableCommand):
    """Long-running APScheduler job runner."""

    async def run(self, args: Namespace) -> None:
        print(f"[scheduler] starting with database: {args.db_url}")

        core_container = await ApplicationFactory(database_url=args.db_url).build()

        scheduler = core_container.scheduler_service()

        import signal

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, scheduler.stop)
        loop.add_signal_handler(signal.SIGINT, scheduler.stop)

        await scheduler.start()

        print("[scheduler] running... (Ctrl+C to stop)")
        try:
            while scheduler.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            scheduler.stop()
        print("[scheduler] stopped")
