from __future__ import annotations

from datetime import UTC, datetime

import pytest
from shell.domain.platform.value_objects.timestamp import Timestamp


class TestTimestamp:
    def test_now_is_utc(self) -> None:
        ts = Timestamp.now()
        assert ts.value.tzinfo == UTC

    def test_naive_raises(self) -> None:
        with pytest.raises(ValueError):
            Timestamp(datetime(2024, 1, 1))
