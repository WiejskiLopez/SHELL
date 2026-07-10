from __future__ import annotations

import json
import logging

from shell.platform.infrastructure.logging.stdlib_logger import JsonFormatter, set_correlation_id


class TestJsonFormatter:
    def _make_record(self, msg: str, level: int = logging.INFO) -> logging.LogRecord:
        record = logging.LogRecord(
            name="test", level=level, pathname="", lineno=0, msg=msg, args=(), exc_info=None
        )
        return record

    def test_output_is_valid_json(self) -> None:
        fmt = JsonFormatter()
        record = self._make_record("test message")
        output = fmt.format(record)
        data = json.loads(output)
        assert data["msg"] == "test message"
        assert "ts" in data
        assert "level" in data

    def test_includes_correlation_id(self) -> None:
        set_correlation_id("req-42")
        fmt = JsonFormatter()
        record = self._make_record("msg")
        data = json.loads(fmt.format(record))
        assert data["correlation_id"] == "req-42"
        set_correlation_id("")

    def test_correlation_id_default_empty(self) -> None:
        set_correlation_id("")
        fmt = JsonFormatter()
        record = self._make_record("msg")
        data = json.loads(fmt.format(record))
        assert data["correlation_id"] == ""
