from __future__ import annotations

from shell.platform.infrastructure.cli.retention import run_retention_cli
from shell.scheduling_service.infrastructure.scheduling.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)


def main() -> None:
    run_retention_cli("scheduling_service", PERSISTENCE_DELIVERY_MODELS)


if __name__ == "__main__":
    main()
