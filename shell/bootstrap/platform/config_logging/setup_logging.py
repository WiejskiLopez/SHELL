from __future__ import annotations

import logging
import sys

from shell.infrastructure.platform.logging.stdlib_logger import JsonFormatter


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
        force=True,
    )
