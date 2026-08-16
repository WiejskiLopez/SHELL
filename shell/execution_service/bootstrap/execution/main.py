from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import uvicorn

from shell.execution_service.bootstrap.execution.container.execution_core_container import (
    ExecutionCoreContainer,
    configure_execution_container,
)
from shell.execution_service.framework.execution.api.app import create_execution_app
from shell.execution_service.infrastructure.execution.seed import seed_execution_dev_data
from shell.execution_service.migrations.baseline import run_execution_baseline
from shell.platform.infrastructure.configuration.shell_config import ShellConfig
from shell.platform.infrastructure.messaging.event.event_worker import run_delivery_workers


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Execution BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8007)
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")
    database_url = args.db_url or config.database_url
    container = ExecutionCoreContainer()
    container.config.db_url.from_value(database_url)
    container.config.broker_url.from_value(config.events.broker_url)
    container.config.worker_id.from_value("execution-event-processor")
    container.config.command_worker_id.from_value("execution-command-processor")
    container.config.worker_heartbeat_interval_seconds.from_value(
        config.events.worker_heartbeat_interval_seconds
    )
    container.config.worker_max_batch_time_seconds.from_value(
        config.events.worker_max_batch_time_seconds
    )
    configure_execution_container(container)
    app = create_execution_app(container, include_routes=True)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port))

    async def run() -> None:
        await run_execution_baseline(database_url)
        if config.seed_dev_data:
            await seed_execution_dev_data(database_url)
        if args.worker:
            await run_delivery_workers(
                workers=(
                    (
                        container.rabbit_inbox_consumer_factory(),
                        container.event_inbox_processor_factory(),
                        container.config.worker_id(),
                    ),
                    (
                        container.rabbit_command_inbox_consumer_factory(),
                        container.command_inbox_processor_factory(),
                        container.config.command_worker_id(),
                    ),
                ),
                session_factory=container.session_factory(),
                heartbeat_model=container.persistence_delivery_models().worker_heartbeat,
                poll_interval_seconds=config.events.worker_poll_interval,
            )
            return
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
