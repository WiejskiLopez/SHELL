"""Entrypoint for the standalone Definition bounded context API."""

from __future__ import annotations

import argparse
import asyncio

import uvicorn

from shell.definition.bootstrap.definition.container.definition_core_container import (
    DefinitionCoreContainer,
)
from shell.definition.framework.definition.api.app import create_definition_app
from shell.definition.migrations.baseline import run_definition_baseline
from shell.platform.infrastructure.configuration.shell_config import ShellConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Definition BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--db-url", default=None)
    args = parser.parse_args()

    config = ShellConfig.from_environment()
    database_url = args.db_url or config.database_url
    container = DefinitionCoreContainer()
    container.config.db_url.from_value(database_url)
    app = create_definition_app(container)
    server = uvicorn.Server(
        uvicorn.Config(app, host=args.host, port=args.port, reload=args.reload)
    )

    async def run() -> None:
        await run_definition_baseline(database_url)
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
