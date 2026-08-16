"""Koncept: reguła architektoniczna dotycząca snapshot ownership: test snapshots are defined in a bounded context domain.

Reguła: test sprawdza kontrakt architektoniczny snapshot ownership: test snapshots are defined in a bounded context domain.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import BASE, architecture_assertion_message, parse_file

if TYPE_CHECKING:
    from pathlib import Path
_BCS = frozenset(
    {"execution", "definition", "session", "user", "project", "scheduling", "messaging"}
)


def _production_python_files() -> list[Path]:
    return [
        path
        for path in BASE.rglob("*.py")
        if not any(
            excluded in path.parts
            for excluded in {"tests", ".venv", "__pycache__", ".pytest_cache", ".opencode"}
        )
    ]


def _bc_for_path(path: Path) -> str | None:
    relative = path.relative_to(BASE)
    return relative.parts[0] if relative.parts and relative.parts[0] in _BCS else None


def _module_name(path: Path) -> str:
    relative = path.relative_to(BASE).with_suffix("")
    return "shell." + ".".join(relative.parts)


def _snapshot_modules() -> dict[str, str]:
    modules: dict[str, str] = {}
    for path in _production_python_files():
        tree = parse_file(path)
        if tree is None:
            continue
        module = _module_name(path)
        has_snapshot_symbol = any(
            isinstance(node, ast.ClassDef) and node.name.endswith("Snapshot")
            for node in ast.walk(tree)
        )
        if has_snapshot_symbol or "snapshot" in path.stem.lower():
            bc = _bc_for_path(path)
            if bc is not None:
                modules[module] = bc
    return modules


def test_snapshots_are_defined_in_a_bounded_context_domain() -> None:
    violations: list[str] = []
    for path in _production_python_files():
        tree = parse_file(path)
        if tree is None:
            continue
        has_snapshot_symbol = any(
            isinstance(node, ast.ClassDef) and node.name.endswith("Snapshot")
            for node in ast.walk(tree)
        )
        if not (has_snapshot_symbol or "snapshot" in path.stem.lower()):
            continue
        relative = path.relative_to(BASE).as_posix()
        bc = _bc_for_path(path)
        if bc is None or "/domain/" not in f"/{relative}":
            violations.append(f"{relative}: snapshot must be defined in shell/<bc>/domain/")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_snapshots_are_defined_in_a_bounded_context_domain",
        "warunek zapisany w asercji musi być spełniony",
        "Snapshot ownership violations:\n" + "\n".join(violations),
    )
