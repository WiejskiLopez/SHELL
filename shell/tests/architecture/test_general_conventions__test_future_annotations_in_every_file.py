"""Koncept: reguła architektoniczna dotycząca general conventions: test future annotations in every file.

Reguła: test sprawdza kontrakt architektoniczny general conventions: test future annotations in every file.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files, parse_file

_KNOWN_MISSING_FUTURE: frozenset[str] = frozenset({})
_PATHS_WITHOUT_TYPE_HINTS: frozenset[str] = frozenset({})
_KNOWN_INIT_DEFINITIONS: frozenset[str] = frozenset({})
_NOQA_KNOWN_INVALID: frozenset[str] = frozenset({})
_NOQA_KNOWN_WITHOUT_REASON: frozenset[str] = frozenset({})
_COMMENT_KNOWN_EXCEPTIONS: frozenset[str] = frozenset({})


def test_future_annotations_in_every_file() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel in _KNOWN_MISSING_FUTURE:
            continue
        if (
            "tests" in rel
            or rel.startswith("config/")
            or rel.startswith("shell.egg-info/")
            or rel.startswith(".venv/")
        ):
            continue
        if "migrations/versions" in rel:
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        has_future = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
            for node in ast.walk(tree)
        )
        if not has_future:
            violations.append(rel)
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_future_annotations_in_every_file",
        "warunek zapisany w asercji musi być spełniony",
        "Production .py files should have `from __future__ import annotations`:\n"
        + "\n".join(violations),
    )
