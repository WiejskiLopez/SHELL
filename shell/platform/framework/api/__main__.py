"""Entrypoint — uruchamia serwer API.

Usage:
    python -m shell.platform.framework.api
    python -m shell.platform.framework.api --port 8080
    python -m shell.platform.framework.api --reload
"""

from __future__ import annotations

import argparse
import asyncio

import uvicorn

from shell.bootstrap.execution.factory.application_factory import ApplicationFactory
from shell.platform.framework.api.app import create_monolith_app
from shell.platform.infrastructure.configuration.shell_config import ShellConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell API server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--db-url", default=None)
    args = parser.parse_args()

    config = ShellConfig.from_environment()
    if args.db_url:
        config.database_url = args.db_url

    async def _run() -> None:
        container = await ApplicationFactory(config=config).build()
        app = create_monolith_app(core_container=container)
        server = uvicorn.Server(
            uvicorn.Config(
                app,
                host=args.host,
                port=args.port,
                reload=args.reload,
            )
        )
        await server.serve()

    asyncio.run(_run())


if __name__ == "__main__":
    main()
