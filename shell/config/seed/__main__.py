"""CLI entry point for seeding dev data.

Usage:
    python -m shell.config.seed --url sqlite+aiosqlite:///shell_dev.db
    python -m shell.config.seed  # uses SHELL_DATABASE_URL env or fallback
"""

from shell.config.seed.dev_data import main

main()
