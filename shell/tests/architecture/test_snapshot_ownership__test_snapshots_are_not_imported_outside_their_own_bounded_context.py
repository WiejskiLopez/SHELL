"""Koncept: reguła architektoniczna dotycząca snapshot ownership: test snapshots are not imported outside their own bounded context.

Reguła: test sprawdza kontrakt architektoniczny snapshot ownership: test snapshots are not imported outside their own bounded context.

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


def test_snapshots_are_not_imported_outside_their_own_bounded_context() -> None:
    snapshot_modules = _snapshot_modules()
    violations: list[str] = []
    for path in _production_python_files():
        source_bc = _bc_for_path(path)
        if source_bc is None:
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            imported_module: str | None = None
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_module = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_module = alias.name
                    target_bc = next(
                        (
                            owner
                            for module, owner in snapshot_modules.items()
                            if imported_module == module or imported_module.startswith(module + ".")
                        ),
                        None,
                    )
                    if target_bc is not None and target_bc != source_bc:
                        violations.append(
                            f"{path.relative_to(BASE).as_posix()}: imports snapshot module {imported_module!r} owned by BC {target_bc}"
                        )
                continue
            if imported_module is None:
                continue
            target_bc = next(
                (
                    owner
                    for module, owner in snapshot_modules.items()
                    if imported_module == module or imported_module.startswith(module + ".")
                ),
                None,
            )
            if target_bc is not None and target_bc != source_bc:
                violations.append(
                    f"{path.relative_to(BASE).as_posix()}: imports snapshot module {imported_module!r} owned by BC {target_bc}"
                )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_snapshots_are_not_imported_outside_their_own_bounded_context",
        "warunek zapisany w asercji musi być spełniony",
        "Snapshots must not cross bounded-context boundaries:\n" + "\n".join(violations),
    )
