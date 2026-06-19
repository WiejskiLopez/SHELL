from __future__ import annotations

from shell.infrastructure.platform.logging.stdlib_logger import get_correlation_id, set_correlation_id


class TestCorrelationId:
    def test_set_and_get(self) -> None:
        set_correlation_id("abc-123")
        assert get_correlation_id() == "abc-123"
        set_correlation_id("")
