from shell.utils.path.path import PathType
"""Tests for lib/logger/_build_log_path.py and lib/logger/_get_logging_formatter.py

Verifies: correct log path construction, correct formatter pattern.
"""

import logging
import pytest
from datetime import datetime, timezone
from shell.logger.internal._build_log_path import _build_log_path
from shell.logger.internal._make_formatter import _make_formatter

_FIXED_NOW = datetime(2026, 4, 8, 15, 30, 0, tzinfo=timezone.utc)

# --- _build_log_path ---

def test_log_path_is_inside_node_logs_dir(tmp_path):
    log_path = _build_log_path(tmp_path, "INFO", now=_FIXED_NOW)
    assert log_path.parent == tmp_path / "logs"


def test_log_path_filename_contains_level(tmp_path):
    log_path = _build_log_path(tmp_path, "DEBUG", now=_FIXED_NOW)
    assert "debug" in log_path.name


def test_log_path_filename_contains_date(tmp_path):
    log_path = _build_log_path(tmp_path, "INFO", now=_FIXED_NOW)
    assert "2026-04-08" in log_path.name


def test_log_path_filename_contains_hour(tmp_path):
    log_path = _build_log_path(tmp_path, "INFO", now=_FIXED_NOW)
    assert "_15" in log_path.name


def test_log_path_filename_is_lowercase(tmp_path):
    log_path = _build_log_path(tmp_path, "WARNING", now=_FIXED_NOW)
    assert log_path.name == "agent.2026-04-08_15.warning.log"


def test_default_level_is_info(tmp_path):
    log_path = _build_log_path(tmp_path, now=_FIXED_NOW)
    assert "info" in log_path.name


# --- _make_formatter ---

def test_formatter_is_logging_formatter_instance():
    fmt = _make_formatter()
    assert isinstance(fmt, logging.Formatter)


def test_formatter_pattern_contains_levelname():
    fmt = _make_formatter()
    assert "levelname" in fmt._fmt


def test_formatter_pattern_contains_message():
    fmt = _make_formatter()
    assert "message" in fmt._fmt
