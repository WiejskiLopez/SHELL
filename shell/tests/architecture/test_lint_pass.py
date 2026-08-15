"""Architecture test — verify the codebase passes ruff + mypy checks."""

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


def test_mypy_domain_and_application_zero_errors() -> None:
    """Fail if mypy strict finds errors in per-BC domain/application layers."""
    layer_paths = [
        path
        for bc_path in SHELL_PKG.iterdir()
        if bc_path.is_dir()
        for path in (bc_path / "domain", bc_path / "application")
        if path.exists()
    ]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--disable-error-code=type-abstract",
            *[str(path) for path in layer_paths],
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        msg = "mypy strict found errors in per-BC domain/application layers"
        raise AssertionError(msg)
