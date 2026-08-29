from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import uvicorn

from shell.execution_service.bootstrap.execution.container.execution_core_container import (
    ExecutionCoreContainer,
    configure_execution_container,
)
from shell.execution_service.framework.execution.api.app import create_execution_app
from shell.execution_service.infrastructure.execution.seed import seed_execution_dev_data
from shell.execution_service.migrations.baseline import run_execution_baseline
from shell.platform.framework.bootstrap.server import build_service_uvicorn_config
from shell.platform.infrastructure.configuration.shell_config import LoadedConfiguration
from shell.platform.infrastructure.messaging.event.event_worker import run_delivery_workers


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Execution BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8007)
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    config = LoadedConfiguration.from_environment(
        Path(__file__).resolve().parent / "config", service_name="execution"
    )
    deployment = config.deployment
    runtime = config.platform_runtime
    service = config.service
    database_url = (
        args.db_url or os.environ.get("EXECUTION_SERVICE_DATABASE_URL") or deployment.database_url
    )
    broker_url = os.environ.get("EXECUTION_SERVICE_BROKER_URL") or runtime.events.broker_url
    api_key = os.environ.get("EXECUTION_SERVICE_API_KEY") or config.auth.api_key
    if not api_key:
        raise ValueError("EXECUTION_SERVICE_API_KEY is required")
    container = ExecutionCoreContainer()
    container.config.db_url.from_value(database_url)
    container.config.broker_url.from_value(broker_url)
    container.config.definition_service_url.from_value(
        os.environ.get("DEFINITION_SERVICE_URL", "http://shell-definition-api:8002")
    )
    container.config.session_service_url.from_value(
        os.environ.get("SESSION_SERVICE_URL", "http://shell-session-api:8003")
    )
    container.config.definition_service_api_key.from_value(
        os.environ.get("DEFINITION_SERVICE_API_KEY", "")
    )
    container.config.session_service_api_key.from_value(
        os.environ.get("SESSION_SERVICE_API_KEY", "")
    )
    container.config.service_http_timeout.from_value(
        float(os.environ.get("SERVICE_HTTP_TIMEOUT", "5"))
    )
    container.config.worker_id.from_value("execution-event-processor")
    container.config.command_worker_id.from_value("execution-command-processor")
    container.config.worker_heartbeat_interval_seconds.from_value(
        runtime.events.worker_heartbeat_interval_seconds
    )
    container.config.worker_max_batch_time_seconds.from_value(
        runtime.events.worker_max_batch_time_seconds
    )
    configure_execution_container(container)
    app = create_execution_app(container, include_routes=True, api_key=api_key)
    server = uvicorn.Server(
        build_service_uvicorn_config(app, service="execution", host=args.host, port=args.port)
    )

    async def run() -> None:
        await run_execution_baseline(database_url)
        if service.seed_dev_data:
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
                poll_interval_seconds=runtime.events.worker_poll_interval,
                outbox_relay=container.outbox_to_transport_relay_factory(),
                outbox_worker_id="execution-outbox-relay",
            )
            return
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
