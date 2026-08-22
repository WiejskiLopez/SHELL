from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import uvicorn

from shell.platform.infrastructure.configuration.shell_config import LoadedConfiguration
from shell.platform.infrastructure.messaging.event.event_worker import run_delivery_workers
from shell.project_service.bootstrap.project.container.project_core_container import (
    ProjectCoreContainer,
    configure_project_container,
)
from shell.project_service.framework.project.project.api.app import create_project_app
from shell.project_service.infrastructure.project.seed import seed_project_dev_data
from shell.project_service.migrations.baseline import run_project_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Project BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8005)
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    config = LoadedConfiguration.from_environment(Path(__file__).resolve().parent / "config")
    deployment = config.deployment
    runtime = config.platform_runtime
    service = config.service
    database_url = args.db_url or deployment.database_url
    container = ProjectCoreContainer()
    container.config.db_url.from_value(database_url)
    container.config.broker_url.from_value(runtime.events.broker_url)
    container.config.worker_id.from_value("project-event-processor")
    container.config.command_worker_id.from_value("project-command-processor")
    container.config.worker_heartbeat_interval_seconds.from_value(
        runtime.events.worker_heartbeat_interval_seconds
    )
    container.config.worker_max_batch_time_seconds.from_value(
        runtime.events.worker_max_batch_time_seconds
    )
    configure_project_container(container)
    app = create_project_app(container)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port))

    async def run() -> None:
        await run_project_baseline(database_url)
        if service.seed_dev_data:
            await seed_project_dev_data(database_url)
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
                poll_interval_seconds=runtime.events.worker_poll_interval,
                outbox_relay=container.outbox_to_transport_relay_factory(),
                outbox_worker_id="project-outbox-relay",
            )
            return
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
