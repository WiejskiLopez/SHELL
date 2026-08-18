from __future__ import annotations

from shell.execution_service.infrastructure.execution.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.platform.infrastructure.cli.retention import run_retention_cli


def main() -> None:
    run_retention_cli("execution_service", PERSISTENCE_DELIVERY_MODELS)


if __name__ == "__main__":
    main()
