from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import uvicorn

from shell.platform.infrastructure.configuration.shell_config import ShellConfig
from shell.scheduling.bootstrap.scheduling.container.scheduling_core_container import (
    SchedulingCoreContainer,
    configure_scheduling_container,
)
from shell.scheduling.framework.scheduling.api.app import create_scheduling_app
from shell.scheduling.migrations.baseline import run_scheduling_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Scheduling BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8006)
    parser.add_argument("--db-url", default=None)
    args = parser.parse_args()
    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")
    database_url = args.db_url or config.database_url
    container = SchedulingCoreContainer()
    container.config.db_url.from_value(database_url)
    configure_scheduling_container(container)
    app = create_scheduling_app(container)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port))

    async def run() -> None:
        await run_scheduling_baseline(database_url)
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()