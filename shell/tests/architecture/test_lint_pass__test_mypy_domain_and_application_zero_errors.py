"""Koncept: reguła architektoniczna dotycząca lint pass: test mypy domain and application zero errors.

Reguła: test sprawdza kontrakt architektoniczny lint pass: test mypy domain and application zero errors.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SHELL_PKG = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = SHELL_PKG.parent


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
