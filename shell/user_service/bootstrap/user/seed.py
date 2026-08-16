"""CLI entry point for seeding the User bounded context dev data.

Usage:
    python -m shell.user_service.bootstrap.user.seed --url sqlite+aiosqlite:///database/dev/user.db
    python -m shell.user_service.bootstrap.user.seed --reset-db
    python -m shell.user_service.bootstrap.user.seed  # uses BC dev config
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from shell.platform.infrastructure.configuration.shell_config import ShellConfig
from shell.user_service.infrastructure.user.seed import seed_user_dev_data


def main() -> None:
    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")
    parser = argparse.ArgumentParser(description="Seed User BC dev data")
    parser.add_argument(
        "--url",
        default=os.environ.get("SHELL_DATABASE_URL") or config.database_url,
        help="Database URL (default: SHELL_DATABASE_URL env or BC dev config)",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Drop and recreate the schema before seeding",
    )
    args = parser.parse_args()

    asyncio.run(seed_user_dev_data(args.url, reset_db=args.reset_db))
    print(f"User BC dev seed data loaded into {args.url}")


if __name__ == "__main__":
    main()
