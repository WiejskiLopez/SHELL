from __future__ import annotations

import tempfile

from shell.platform.framework.cli.parser import parse_args

_TEMP_NODE_DIR = f"{tempfile.gettempdir()}/node"


class TestCliParser:
    def test_parser_defaults(self) -> None:
        ns = parse_args([])
        assert ns.mode is None
        assert ns.node_dir is None
        assert ns.dry_run is False
        assert ns.add_dirs == []

    def test_parser_flags(self) -> None:
        ns = parse_args(
            [
                "--node-dir",
                _TEMP_NODE_DIR,
                "--mode",
                "agent",
                "--model",
                "gpt-4o",
                "--max-step",
                "10",
                "--dry-run",
            ]
        )
        assert ns.node_dir == _TEMP_NODE_DIR
        assert ns.mode == "agent"
        assert ns.model == "gpt-4o"
        assert ns.max_step == 10
        assert ns.dry_run is True
