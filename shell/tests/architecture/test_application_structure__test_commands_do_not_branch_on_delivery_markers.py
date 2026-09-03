"""Koncept: komendy dziedziczą WPROST po Command (bez Sync/Async rozgałęzień).

Reguła: kazda klasa ``*Command`` ma dokładnie jedną klasę bazową ``Command``
i nie dziedziczy po żadnym pochodnym znaczniku (np. ``SyncCommand``,
``AsyncCommand``). Asynchroniczność komendy wynika z portu/wiringu, nigdy z
typu klasy. Kontrprzykład (zabroniony): ``class XAsyncCommand(AsyncCommand)``.

Poprawnie: ``class XCommand(Command)`` — bazą jest wyłącznie ``Command``.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_named_dirs,
    iter_py_files,
    parse_file,
)

_FORBIDDEN_DERIVED_MARKERS = frozenset({"SyncCommand", "AsyncCommand"})


def test_commands_do_not_branch_on_delivery_markers() -> None:
    violations: list[str] = []
    for cmd_dir in iter_named_dirs("application", "commands"):
        for path in iter_py_files(cmd_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not node.name.endswith("Command"):
                    continue
                base_names = {
                    base.id for base in node.bases if isinstance(base, ast.Name)
                }
                extra = base_names - {"Command"}
                if _FORBIDDEN_DERIVED_MARKERS & extra:
                    violations.append(
                        f"{path.relative_to(BASE)}: {node.name} dziedziczy po "
                        f"{sorted(_FORBIDDEN_DERIVED_MARKERS & extra)}"
                    )
    assert not violations, architecture_assertion_message(
        "test_commands_do_not_branch_on_delivery_markers",
        "komendy dziedziczą wyłącznie po Command (bez Sync/Async submarkerów)",
        violations,
    )