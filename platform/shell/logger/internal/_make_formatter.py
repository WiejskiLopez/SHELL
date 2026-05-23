"""_make_formatter.py
Responsible for one thing: creating the shared log formatter.

Format: timestamp | level | message
"""

import logging
from datetime import datetime, timezone


class IsoUtcFormatter(logging.Formatter):
    """Formatter that emits ISO8601 UTC timestamps with milliseconds."""

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        # e.g. 2026-05-01T06:54:17.326Z
        return dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def _make_formatter() -> logging.Formatter:
    return IsoUtcFormatter("%(asctime)s | %(levelname)-8s | %(message)s")
