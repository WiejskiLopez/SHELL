"""Entrypoint for the standalone Session bounded context API."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import uvicorn

from shell.platform.infrastructure.configuration.shell_config import LoadedConfiguration
from shell.platform.infrastructure.messaging.event.event_worker import run_delivery_workers
from shell.session_service.bootstrap.session.container.session_core_container import (
    SessionCoreContainer,
    configure_session_container,
)
from shell.session_service.framework.session.api.app import create_session_app
from shell.session_service.infrastructure.session.seed import seed_session_dev_data
from shell.session_service.migrations.baseline import run_session_baseline


async def _run_event_worker(container: SessionCoreContainer) -> None:
    """Consume cross-BC events from the broker and process the local inbox."""
    config = LoadedConfiguration.from_environment(Path(__file__).resolve().parent / "config")
    runtime = config.platform_runtime

    await run_delivery_workers(
        workers=(
            (
                container.rabbit_inbox_consumer_factory(),
                container.event_inbox_processor_factory(),
                "session-event-processor",
            ),
            (
                container.rabbit_command_inbox_consumer_factory(),
                container.command_inbox_processor_factory(),
                "session-command-processor",
            ),
        ),
        session_factory=container.session_factory(),
        heartbeat_model=container.persistence_delivery_models().worker_heartbeat,
        poll_interval_seconds=runtime.events.worker_poll_interval,
        outbox_relay=container.outbox_to_transport_relay_factory(),
        outbox_worker_id="session-outbox-relay",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Session BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8003)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    config = LoadedConfiguration.from_environment(Path(__file__).resolve().parent / "config")
    deployment = config.deployment
    runtime = config.platform_runtime
    service = config.service
    database_url = (
        args.db_url
        or os.environ.get("SESSION_SERVICE_DATABASE_URL")
        or deployment.database_url
    )
    broker_url = os.environ.get("SESSION_SERVICE_BROKER_URL") or runtime.events.broker_url
    api_key = os.environ.get("SESSION_SERVICE_API_KEY") or config.auth.api_key
    if not api_key:
        raise ValueError("SESSION_SERVICE_API_KEY is required")
    container = SessionCoreContainer()
    container.config.db_url.from_value(database_url)
    container.config.broker_url.from_value(broker_url)
    container.config.worker_heartbeat_interval_seconds.from_value(
        runtime.events.worker_heartbeat_interval_seconds
    )
    container.config.worker_max_batch_time_seconds.from_value(
        runtime.events.worker_max_batch_time_seconds
    )
    container.config.worker_id.from_value("session-event-processor")
    container.config.command_worker_id.from_value("session-command-processor")
    configure_session_container(container)
    app = create_session_app(container, api_key=api_key)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port, reload=args.reload))

    async def run() -> None:
        await run_session_baseline(database_url)
        if service.seed_dev_data:
            await seed_session_dev_data(database_url)
        if args.worker:
            await _run_event_worker(container)
        else:
            await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
