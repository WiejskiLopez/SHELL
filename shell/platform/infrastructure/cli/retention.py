"""shell-retention — controlled cleanup of DLQ and processed_delivery rows.

Runs the bounded-context retention policy as an explicit, auditable task
(ref4.md Krok 6): purges only rows older than the configured window and prints
the resulting report so a scheduler/cron can capture the metric.

Example:
    shell-retention --bc session --db-url sqlite+aiosqlite:///session.db \
        --dead-letter-days 90 --processed-delivery-days 30
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import logging
import os
from typing import Any, cast

from shell.platform.infrastructure.messaging.inbox.delivery_retention_service import (
    DeliveryRetentionService,
    RetentionReport,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory

logger = logging.getLogger(__name__)

_BCS = (
    "definition_service",
    "execution_service",
    "ingestion_service",
    "project_service",
    "scheduling_service",
    "session_service",
    "user_service",
)


def _models_for(bc: str) -> Any:
    """Import a BC's persistence delivery models via importlib (CLI bootstrap tool).

    Dynamic import keeps the platform free of static bounded-context imports.
    """
    layer = bc.removesuffix("_service")
    module_name = f"shell.{bc}.infrastructure.{layer}.persistence.sql.models.base"
    module = cast("Any", importlib.import_module(module_name))
    return module.PERSISTENCE_DELIVERY_MODELS


async def purge_for_bounded_context(
    bounded_context: str,
    db_url: str,
    *,
    dead_letter_retention_days: int = 90,
    processed_delivery_retention_days: int = 30,
) -> RetentionReport:
    """Run the retention policy for one bounded context (testable entrypoint)."""
    models = _models_for(bounded_context)
    service = DeliveryRetentionService(
        build_session_factory(db_url),
        cast("type[Any]", models.events.inbox),
        cast("type[Any]", models.processed_delivery),
        dead_letter_retention_days=dead_letter_retention_days,
        processed_delivery_retention_days=processed_delivery_retention_days,
    )
    return await service.purge_expired()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="shell-retention",
        description="Purge expired DLQ and processed_delivery rows for a bounded context.",
    )
    parser.add_argument("--bc", required=True, choices=_BCS, help="bounded context name")
    parser.add_argument("--db-url", default=None, help="database URL (default: SHELL_DATABASE_URL)")
    parser.add_argument("--dead-letter-days", type=int, default=90)
    parser.add_argument("--processed-delivery-days", type=int, default=30)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    db_url = (
        args.db_url
        or os.environ.get("SHELL_DATABASE_URL")
        or f"sqlite+aiosqlite:///shell-{args.bc}.db"
    )
    report = asyncio.run(
        purge_for_bounded_context(
            args.bc,
            db_url,
            dead_letter_retention_days=args.dead_letter_days,
            processed_delivery_retention_days=args.processed_delivery_days,
        )
    )
    print(
        "retention bc=%s purged_dead_letter=%s purged_processed_delivery=%s "
        "kept_dead_letter=%s kept_processed_delivery=%s detail=%s",
        args.bc,
        report.purged_dead_letter,
        report.purged_processed_delivery,
        report.kept_dead_letter,
        report.kept_processed_delivery,
        report.detail,
    )


if __name__ == "__main__":
    main()
