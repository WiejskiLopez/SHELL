"""CLI entry point for seeding the Scheduling bounded context dev data.

Usage:
    python -m shell.scheduling_service.bootstrap.scheduling.seed --url sqlite+aiosqlite:///shell/scheduling_service/docker/dev_db/scheduling.db
    python -m shell.scheduling_service.bootstrap.scheduling.seed --reset-db
    python -m shell.scheduling_service.bootstrap.scheduling.seed  # uses BC dev config
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from shell.platform.infrastructure.configuration.shell_config import ShellConfig
from shell.scheduling_service.infrastructure.scheduling.seed import seed_scheduling_dev_data


def main() -> None:
    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")
    parser = argparse.ArgumentParser(description="Seed Scheduling BC dev data")
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

    asyncio.run(seed_scheduling_dev_data(args.url, reset_db=args.reset_db))
    print(f"Scheduling BC dev seed data loaded into {args.url}")


if __name__ == "__main__":
    main()
