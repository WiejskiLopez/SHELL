"""Entrypoint for the standalone Session bounded context API."""

from __future__ import annotations

import argparse
import asyncio

import uvicorn

from shell.platform.infrastructure.configuration.shell_config import ShellConfig
from shell.session.bootstrap.session.container.session_core_container import (
    SessionCoreContainer,
    configure_session_container,
)
from shell.session.framework.session.api.app import create_session_app
from shell.session.migrations.baseline import run_session_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Session BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8003)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--db-url", default=None)
    args = parser.parse_args()
    config = ShellConfig.from_environment()
    database_url = args.db_url or config.database_url
    container = SessionCoreContainer()
    container.config.db_url.from_value(database_url)
    configure_session_container(container)
    app = create_session_app(container)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port, reload=args.reload))

    async def run() -> None:
        await run_session_baseline(database_url)
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
