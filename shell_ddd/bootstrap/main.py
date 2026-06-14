import argparse
import asyncio
import sys

from shell_ddd.bootstrap.cli.command.relay_command import RelayCommand
from shell_ddd.bootstrap.cli.command.smoke_command import SmokeCommand
from shell_ddd.bootstrap.config_logging.setup_logging import setup_logging


def main() -> int:
    setup_logging()

    parser = argparse.ArgumentParser(description="Shell DDD Admin CLI")
    parser.add_argument("command", choices=["smoke", "relay"], help="Command to execute")
    parser.add_argument("--db-url", default="sqlite+aiosqlite:///shell_ddd.db", help="Database URL")

    args = parser.parse_args()

    # Rejestr poleceń (Command Registry)
    commands = {
        "smoke": SmokeCommand(),
        "relay": RelayCommand()
    }

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
