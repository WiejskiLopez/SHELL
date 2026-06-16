"""Production background worker command."""
import asyncio
from argparse import Namespace

from shell.bootstrap.cli.command.command import RunnableCommand
from shell.bootstrap.factory.application_factory import ApplicationFactory


class WorkerCommand(RunnableCommand):
    """Long-running worker: OutboxRelay → InboxProcessor loop."""

    async def run(self, args: Namespace) -> None:
        print(f"[worker] starting with database: {args.db_url}")

        # Build full container with wiring
        core_container = await ApplicationFactory(database_url=args.db_url).build()

        # Get worker from container
        worker = core_container.messaging.messaging_worker()

        # Handle shutdown signals
        import signal
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, worker.stop)

        print("[worker] running... (Ctrl+C to stop)")
        await worker.run()
        print("[worker] stopped")