from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import uvicorn

from shell.execution.bootstrap.execution.container.execution_core_container import (
    ExecutionCoreContainer,
    configure_execution_container,
)
from shell.execution.framework.execution.api.app import create_execution_app
from shell.execution.migrations.baseline import run_execution_baseline
from shell.platform.infrastructure.configuration.shell_config import ShellConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Execution BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8007)
    parser.add_argument("--db-url", default=None)
    args = parser.parse_args()
    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")
    database_url = args.db_url or config.database_url
    container = ExecutionCoreContainer()
    container.config.db_url.from_value(database_url)
    configure_execution_container(container)
    app = create_execution_app(container, include_routes=True)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port))

    async def run() -> None:
        await run_execution_baseline(database_url)
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()