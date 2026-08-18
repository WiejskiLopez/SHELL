"""Generic retention CLI primitives for service-owned entry points."""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any

from shell.platform.infrastructure.messaging.inbox.delivery_retention_service import (
    DeliveryRetentionService,
    RetentionReport,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory


async def purge_with_models(
    session_factory: Any,
    inbox_model: type[Any],
    processed_delivery_model: type[Any],
    *,
    dead_letter_retention_days: int = 90,
    processed_delivery_retention_days: int = 30,
) -> RetentionReport:
    """Run retention using models supplied by the owning service."""
    service = DeliveryRetentionService(
        session_factory,
        inbox_model,
        processed_delivery_model,
        dead_letter_retention_days=dead_letter_retention_days,
        processed_delivery_retention_days=processed_delivery_retention_days,
    )
    return await service.purge_expired()


def run_retention_cli(service_name: str, models: Any) -> None:
    """Run the shared retention CLI with service-owned delivery models."""
    parser = argparse.ArgumentParser(
        prog=f"shell-retention-{service_name.removesuffix('_service')}",
        description="Purge expired DLQ and processed_delivery rows.",
    )
    parser.add_argument("--db-url", default=None, help="database URL (default: SHELL_DATABASE_URL)")
    parser.add_argument("--dead-letter-days", type=int, default=90)
    parser.add_argument("--processed-delivery-days", type=int, default=30)
    args = parser.parse_args()

    db_url = (
        args.db_url
        or os.environ.get("SHELL_DATABASE_URL")
        or f"sqlite+aiosqlite:///{service_name}.db"
    )
    report = asyncio.run(
        purge_with_models(
            build_session_factory(db_url),
            models.events.inbox,
            models.processed_delivery,
            dead_letter_retention_days=args.dead_letter_days,
            processed_delivery_retention_days=args.processed_delivery_days,
        )
    )
    print(
        f"retention service={service_name} "
        f"purged_dead_letter={report.purged_dead_letter} "
        f"purged_processed_delivery={report.purged_processed_delivery} "
        f"kept_dead_letter={report.kept_dead_letter} "
        f"kept_processed_delivery={report.kept_processed_delivery} "
        f"detail={report.detail}"
    )


__all__ = ["purge_with_models", "run_retention_cli"]
