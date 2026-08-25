#!/usr/bin/env python
"""Generate an Alembic baseline from one service's ORM metadata."""

from __future__ import annotations

import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--migrations-dir", type=Path, required=True)
    parser.add_argument("--service-package", required=True)
    parser.add_argument("--base-class", required=True)
    parser.add_argument("--database-url", required=True)
    args = parser.parse_args()
    config = Config()
    config.set_main_option("script_location", str(args.migrations_dir.resolve()))
    config.set_main_option("sqlalchemy.url", args.database_url)
    config.set_main_option("service_package", args.service_package)
    config.set_main_option("base_class", args.base_class)
    command.revision(config, message="initial service schema", autogenerate=True, head="base")


if __name__ == "__main__":
    main()