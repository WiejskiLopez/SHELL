from __future__ import annotations


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
                "/tmp/node",
                "--mode",
                "agent",
                "--model",
                "gpt-4o",
                "--max-step",
                "10",
                "--dry-run",
            ]
        )
        assert ns.node_dir == "/tmp/node"
        assert ns.mode == "agent"
        assert ns.model == "gpt-4o"
        assert ns.max_step == 10
        assert ns.dry_run is True
