from __future__ import annotations

from shell.framework.platform.cli.main import main


class TestCliMain:
    def test_main_no_args_returns_1(self) -> None:
        assert main([]) == 1

    def test_main_unknown_mode_returns_1(self) -> None:
        assert main(["unknown_mode"]) == 1
