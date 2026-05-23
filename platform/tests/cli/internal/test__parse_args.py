"""Tests for lib/args/_parse_args.py

Verifies that raw CLI argument parsing produces the correct Namespace values.
"""

import pytest
from shell.component.cli.cli.internal._parse_args import _parse_args


def test_no_args_produces_safe_defaults():
    ns = _parse_args([])
    assert ns.node_dir is None
    assert ns.version is False
    assert ns.clean is False
    assert ns.clean_out is False
    assert ns.dry_run is False
    assert ns.log_level is None
    assert ns.no_ask_user is False
    assert ns.autopilot is False
    assert ns.add_dirs == []
    assert ns.prompt is None


def test_node_flag_is_captured():
    ns = _parse_args(["--node-dir", "/some/path"])
    assert ns.node_dir == "/some/path"


def test_boolean_flags_are_set():
    ns = _parse_args(["--version", "--clean", "--dry-run", "--no-ask-user", "--autopilot"])
    assert ns.version is True
    assert ns.clean is True
    assert ns.dry_run is True
    assert ns.no_ask_user is True
    assert ns.autopilot is True


def test_log_level_is_captured():
    ns = _parse_args(["--log-level", "DEBUG"])
    assert ns.log_level == "DEBUG"


def test_add_dir_accumulates_multiple_values():
    ns = _parse_args(["--add-dir", "/a", "--add-dir", "/b"])
    assert ns.add_dirs == ["/a", "/b"]


def test_prompt_flag_is_captured():
    ns = _parse_args(["--prompt", "do the thing"])
    assert ns.prompt == "do the thing"


def test_clean_out_flag():
    ns = _parse_args(["--clean-out"])
    assert ns.clean_out is True
