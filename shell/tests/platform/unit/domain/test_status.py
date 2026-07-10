from __future__ import annotations

import pytest

from shell.platform.domain.value_objects.status import Status


class TestStatus:
    def test_sentinels(self) -> None:
        assert Status.idle().value == "idle"
        assert Status.running().value == "running"
        assert Status.done().value == "done"
        assert Status.failed().value == "failed"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            Status("")
