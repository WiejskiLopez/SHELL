from __future__ import annotations

import argparse
import asyncio

import uvicorn

from shell.platform.infrastructure.configuration.shell_config import ShellConfig
from shell.project.bootstrap.project.container.project_core_container import (
    ProjectCoreContainer,
    configure_project_container,
)
from shell.project.framework.project.project.api.app import create_project_app
from shell.project.migrations.baseline import run_project_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Project BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8005)
    parser.add_argument("--db-url", default=None)
    args = parser.parse_args()
    config = ShellConfig.from_environment()
    database_url = args.db_url or config.database_url
    container = ProjectCoreContainer()
    container.config.db_url.from_value(database_url)
    configure_project_container(container)
    app = create_project_app(container)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port))

    async def run() -> None:
        await run_project_baseline(database_url)
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
