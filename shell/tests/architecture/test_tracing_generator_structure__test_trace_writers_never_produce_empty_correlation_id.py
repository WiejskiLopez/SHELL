"""Koncept: writerzy trace nie produkują pustego correlation_id.

Reguła: pliki zapisujące trace do outboxa/komendy (mapper, command outbox
writers/publisher) muszą używać ``get_or_create_correlation_id()`` zamiast
surowego ``get_correlation_id()`` — surowy getter może zwrócić pusty ciąg i
zerwać korelację.

Poprawnie: każdy z tych plików wywołuje ``get_or_create_correlation_id()``.
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files, parse_file

_TRACE_WRITER_SUBSTRINGS: tuple[str, ...] = (
    "infrastructure/mapping/reflective_integration_mapper.py",
    "infrastructure/messaging/command/sql_command_outbox_writer.py",
)


def _uses_bare_get_correlation(tree: ast.Module) -> bool:
    """Czy moduł wywołuje surowy get_correlation_id (read-only, może zwrócić \"\")."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "get_correlation_id":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "get_correlation_id":
                return True
    return False


def _uses_get_or_create(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "get_or_create_correlation_id":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "get_or_create_correlation_id":
                return True
    return False


def test_trace_writers_never_produce_empty_correlation_id() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "platform"):
        rel = str(path.relative_to(BASE))
        if not any(sub in rel for sub in _TRACE_WRITER_SUBSTRINGS):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        if _uses_bare_get_correlation(tree) and not _uses_get_or_create(tree):
            violations.append(rel)
    assert not violations, architecture_assertion_message(
        "test_trace_writers_never_produce_empty_correlation_id",
        "writerzy trace muszą używać get_or_create_correlation_id()",
        violations,
    )
