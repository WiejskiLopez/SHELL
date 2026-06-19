from __future__ import annotations

import logging

from shell.tests.conftest import _spy_logger


class TestStdlibLogger:
    def test_info_writes_to_logger(self) -> None:
        logger, records = _spy_logger("test_stdlib_info")
        logger.info("hello world")
        assert any("hello world" in r.getMessage() for r in records)

    def test_warning_level(self) -> None:
        logger, records = _spy_logger("test_stdlib_warn")
        logger.warning("watch out")
        assert any(r.levelno == logging.WARNING for r in records)

    def test_error_level(self) -> None:
        logger, records = _spy_logger("test_stdlib_err")
        logger.error("boom")
        assert any(r.levelno == logging.ERROR for r in records)

    def test_debug_level(self) -> None:
        logger, records = _spy_logger("test_stdlib_dbg", level=logging.DEBUG)
        logger.debug("trace")
        assert any(r.levelno == logging.DEBUG for r in records)
