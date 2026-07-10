from __future__ import annotations

import argparse
import asyncio
import sys

from shell.bootstrap.execution.cli.command.relay_command import RelayCommand
from shell.bootstrap.execution.cli.command.smoke_command import SmokeCommand
from shell.platform.bootstrap.config_logging.setup_logging import setup_logging
from shell.platform.infrastructure.configuration.shell_config import ShellConfig


def main() -> int:
    setup_logging()

    parser = argparse.ArgumentParser(description="Shell DDD Admin CLI")
    parser.add_argument("command", choices=["smoke", "relay"], help="Command to execute")
    parser.add_argument("--db-url", default=None, help="Database URL (overrides config)")

    args = parser.parse_args()

    config = ShellConfig.from_environment()
    if args.db_url:
        config.database_url = args.db_url

    args.shell_config = config

    commands = {"smoke": SmokeCommand(), "relay": RelayCommand()}

    command = commands.get(args.command)
    if not command:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    try:
        asyncio.run(command.run(args))
        return 0
    except Exception as e:
        print(f"Execution failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
