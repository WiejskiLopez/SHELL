"""Koncept: reguła architektoniczna dotycząca tracing context structure.

Reguła: test sprawdza kontrakt architektoniczny tracing context structure.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files, parse_file

_OUTBOX_EVENT_CALLS: set[str] = set()
_OUTBOX_MESSAGE_CALLS: set[str] = set()

def _check_outbox_call(node: ast.Call, path: str, line: int) -> str | None:
    if not isinstance(node.func, ast.Name):
        return None
    if node.func.id not in ('OutboxEventModel', 'OutboxMessageModel'):
        return None
    kwargs = {kw.arg for kw in node.keywords if kw.arg is not None}
    missing: list[str] = []
    if 'correlation_id' not in kwargs:
        missing.append('correlation_id')
    if 'causation_id' not in kwargs:
        missing.append('causation_id')
    if not missing:
        return None
    return f"{path}:{line}: {node.func.id}() bez {', '.join(missing)}"

def test_outbox_models_always_have_correlation_and_causation() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        tree = parse_file(path)
        if tree is None:
            continue
        rel = path.relative_to(BASE)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                violation = _check_outbox_call(node, str(rel), node.lineno)
                if violation:
                    violations.append(violation)
    assert not violations, architecture_assertion_message('reguła testowana przez test_outbox_models_always_have_correlation_and_causation', 'warunek zapisany w asercji musi być spełniony', 'Naruszona reguła: modele outboxa muszą propagować correlation_id i causation_id.\nZnaleziono:\n' + '\n'.join(violations) + '\nJak naprawić: przekaż oba pola jako argumenty nazwane z kontekstu korelacji i przyczynowości.')
