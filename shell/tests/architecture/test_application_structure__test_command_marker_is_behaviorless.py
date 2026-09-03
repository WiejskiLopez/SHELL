"""Koncept: Command to baza tożsamości komend — jedno pole, zero logiki.

Reguła: klasa ``Command`` w ``platform/application/commands/command.py``
dziedziczy wyłącznie z ``object`` i definiuje wyłącznie pole ``command_id``
(kw_only, automatyczny identyfikator nadawany przy konstrukcji) oraz metodę
``__post_init__`` walidującą niepustość tego identyfikatora. Nie wolno
dokładać żadnych innych pól, metod ani zachowania biznesowego — identyfikator
jest jedyną odpowiedzialnością wspólnej bazy, a funkcja ``_new_command_id``
jest helperem modułowym, nie składową klasy.

Poprawnie: ``Command`` ma dokładnie jedno pole ``command_id`` i ściśle
ograniczony korpus (tylko deklaracja pola + walidacja tożsamości).
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    parse_file,
)

_COMMAND_PATH = BASE / "platform/application/commands/command.py"
_ALLOWED_BASES = frozenset({"object"})
_ALLOWED_ASSIGNS = frozenset({"command_id"})
_ALLOWED_METHODS = frozenset({"__post_init__"})


def test_command_marker_is_behaviorless() -> None:
    tree = parse_file(_COMMAND_PATH)
    assert tree is not None, f"Nie można sparsować {_COMMAND_PATH}"

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "Command":
            continue

        base_names = {base.id for base in node.bases if isinstance(base, ast.Name)}
        unexpected_bases = base_names - _ALLOWED_BASES
        if unexpected_bases:
            violations.append(f"Command dziedziczy po: {sorted(unexpected_bases)}")

        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                target_names = [
                    target.id for target in stmt.targets if isinstance(target, ast.Name)
                ]
                if target_names and not set(target_names).issubset(_ALLOWED_ASSIGNS):
                    violations.append(
                        f"Command definiuje pole {target_names} "
                        f"(dozwolone wyłącznie: {sorted(_ALLOWED_ASSIGNS)})"
                    )
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if stmt.name not in _ALLOWED_METHODS:
                    violations.append(
                        f"Command definiuje metodę {stmt.name} "
                        f"(dozwolone wyłącznie: {sorted(_ALLOWED_METHODS)})"
                    )
            elif isinstance(stmt, ast.ClassDef):
                violations.append(f"Command definiuje klasę zagnieżdżoną {stmt.name}")

    assert not violations, architecture_assertion_message(
        "test_command_marker_is_behaviorless",
        "Command to baza tożsamości: wyłącznie pole command_id i walidacja id",
        violations,
    )