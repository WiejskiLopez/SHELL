"""Koncept: CommandHandler i EventHandler pozostają czystymi znacznikami.

Reguła: klasy ``CommandHandler`` i ``EventHandler`` w
``platform/application/command_handlers`` oraz ``event_handlers`` nie definiują
pól, nie mają konkretnych metod (poza abstrakcyjną deklaracją ``handle``) ani
nie dziedziczą po klasach innych niż ``object``/``ABC``/``Generic``. Znaczniki
muszą pozostać neutralne — nie mogą gromadzić logiki ani konstruktorów.

Poprawnie: oba znaczniki mają ``__slots__ = ()``, abstrakcyjną ``handle``
i pusty korpus (bez pól i logiki).
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    parse_file,
)

_MARKER_FILES = (
    (BASE / "platform/application/command_handlers/command_handler.py", "CommandHandler"),
    (BASE / "platform/application/event_handlers/event_handler.py", "EventHandler"),
)

_ALLOWED_BASES = frozenset({"object", "ABC", "Generic"})


def _is_abstract_handle(stmt: ast.AST) -> bool:
    if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    if stmt.name != "handle":
        return False
    has_abstract = any(
        isinstance(d, ast.Name) and d.id == "abstractmethod" for d in stmt.decorator_list
    )
    return has_abstract


def test_handler_markers_are_behaviorless() -> None:
    violations: list[str] = []
    for path, marker_name in _MARKER_FILES:
        tree = parse_file(path)
        if tree is None:
            violations.append(f"{path.relative_to(BASE)}: nie można sparsować")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name != marker_name:
                continue
            base_names = {
                b.id for b in node.bases if isinstance(b, ast.Name)
            } | {
                b.value.id
                for b in node.bases
                if isinstance(b, ast.Subscript) and isinstance(b.value, ast.Name)
            }
            if base_names - _ALLOWED_BASES:
                violations.append(
                    f"{marker_name}: dziedziczy po {sorted(base_names - _ALLOWED_BASES)}"
                )
            for stmt in node.body:
                if _is_abstract_handle(stmt):
                    # abstrakcyjna deklaracja handle jest dozwolona (kontrakt)
                    continue
                is_slots = (
                    isinstance(stmt, ast.Assign)
                    and any(
                        isinstance(t, ast.Name) and t.id == "__slots__"
                        for t in stmt.targets
                    )
                )
                if is_slots:
                    continue
                if isinstance(
                    stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    violations.append(
                        f"{marker_name}: definiuje składową {stmt.name} (tylko abstrakcyjna handle)"
                    )
                elif isinstance(stmt, ast.Assign):
                    names = [t.id for t in stmt.targets if isinstance(t, ast.Name)]
                    if names:
                        violations.append(f"{marker_name}: definiuje pole {names}")
    assert not violations, architecture_assertion_message(
        "test_handler_markers_are_behaviorless",
        "CommandHandler/EventHandler bez pól, logiki i konkretnych metod",
        violations,
    )