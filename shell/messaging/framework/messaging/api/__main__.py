from __future__ import annotations

import argparse
import asyncio

import uvicorn

from shell.messaging.bootstrap.messaging.container.messaging_core_container import (
    MessagingCoreContainer,
    configure_messaging_container,
)
from shell.messaging.framework.messaging.api.app import create_messaging_app
from shell.messaging.migrations.baseline import run_messaging_baseline
from shell.platform.infrastructure.configuration.shell_config import ShellConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Messaging BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8004)
    parser.add_argument("--db-url", default=None)
    args = parser.parse_args()
    config = ShellConfig.from_environment()
    database_url = args.db_url or config.database_url
    container = MessagingCoreContainer()
    container.config.db_url.from_value(database_url)
    configure_messaging_container(container)
    app = create_messaging_app(container)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port))

    async def run() -> None:
        await run_messaging_baseline(database_url)
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
