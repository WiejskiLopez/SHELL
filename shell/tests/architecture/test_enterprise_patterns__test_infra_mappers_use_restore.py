"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test infra mappers use restore.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test infra mappers use restore.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    iter_domain_files,
    iter_layer_files,
    parse_file,
)

_KNOWN_MAPPER_USES_INIT: frozenset[str] = frozenset({})


def _is_aggregate_root_base(base: ast.AST) -> bool:
    if isinstance(base, ast.Name) and base.id == "AggregateRoot":
        return True
    if isinstance(base, ast.Subscript):
        return _is_aggregate_root_base(base.value)
    return False


def test_infra_mappers_use_restore() -> None:
    violations: list[str] = []
    aggregate_names: set[str] = set()
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                _is_aggregate_root_base(b) for b in node.bases
            ):
                aggregate_names.add(node.name)
    for path in iter_layer_files("infrastructure"):
        if "mappers" not in path.parts and path.name != "mappers.py":
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name not in aggregate_names:
                continue
            has_restore_call = False
            has_init_call = False
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Call):
                    if isinstance(stmt.func, ast.Attribute) and stmt.func.attr == "restore":
                        has_restore_call = True
                    elif isinstance(stmt.func, ast.Name) and stmt.func.id == node.name:
                        has_init_call = True
            if has_init_call and (not has_restore_call):
                key = f"{path.relative_to(BASE).as_posix()}: {node.name}"
                if key not in _KNOWN_MAPPER_USES_INIT:
                    violations.append(key)
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_infra_mappers_use_restore",
        "warunek zapisany w asercji musi być spełniony",
        "Infrastructure mappers should call Aggregate.restore(), not Aggregate(...). Add known violations to _KNOWN_MAPPER_USES_INIT:\n"
        + "\n".join(violations),
    )
