"""Architecture test — verify the codebase passes ruff linting with zero errors."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SHELL_PKG = Path(__file__).resolve().parent.parent.parent  # shell/
PROJECT_ROOT = SHELL_PKG.parent


def test_ruff_zero_errors() -> None:
    """Fail if ruff check finds any violations in the shell/ package."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            str(SHELL_PKG),
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        msg = f"ruff check found {result.returncode} error(s) — run `ruff check shell/` locally"
        raise AssertionError(msg)
