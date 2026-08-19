"""CLI entry point for seeding the Ingestion bounded context dev data.

Usage:
    python -m shell.ingestion_service.bootstrap.ingestion.seed --url sqlite+aiosqlite:///shell/ingestion_service/docker/dev_db/ingestion.db
    python -m shell.ingestion_service.bootstrap.ingestion.seed --reset-db
    python -m shell.ingestion_service.bootstrap.ingestion.seed  # uses BC dev config
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from shell.ingestion_service.infrastructure.ingestion.seed import seed_ingestion_dev_data
from shell.platform.infrastructure.configuration.shell_config import LoadedConfiguration


def main() -> None:
    config = LoadedConfiguration.from_environment(Path(__file__).resolve().parent / "config")
    deployment = config.deployment
    parser = argparse.ArgumentParser(description="Seed Ingestion BC dev data")
    parser.add_argument(
        "--url",
        default=os.environ.get("SHELL_DATABASE_URL") or deployment.database_url,
        help="Database URL (default: SHELL_DATABASE_URL env or BC dev config)",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Drop and recreate the schema before seeding",
    )
    args = parser.parse_args()

    asyncio.run(seed_ingestion_dev_data(args.url, reset_db=args.reset_db))
    print(f"Ingestion BC dev seed data loaded into {args.url}")


if __name__ == "__main__":
    main()
