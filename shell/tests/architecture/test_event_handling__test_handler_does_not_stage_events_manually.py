"""Koncept: reguła architektoniczna dotycząca event handling: test handler does not stage events manually.

Reguła: test sprawdza kontrakt architektoniczny event handling: test handler does not stage events manually.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_py_files,
    parse_file,
)

_UOW_BASES = (BASE / 'infrastructure', BASE / 'user' / 'infrastructure')
_KNOWN_NON_UOW_EXTENDERS: frozenset[str] = frozenset()
_HANDLER_BASES = (BASE / 'application', BASE / 'user' / 'application')

def test_handler_does_not_stage_events_manually() -> None:
    violations: list[str] = []
    for handler_base in _HANDLER_BASES:
        for py_file in iter_py_files(handler_base):
            rel = py_file.relative_to(BASE)
            if 'handler' not in py_file.name and 'handler' not in str(rel):
                continue
            tree = parse_file(py_file)
            if tree is None:
                continue
            for class_node in find_classes(tree):
                if not class_node.name.endswith('Handler'):
                    continue
                for stmt in class_node.body:
                    if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    key = f'{rel}: {class_node.name}.{stmt.name}'
                    source = ast.get_source_segment(py_file.read_text(encoding='utf-8'), stmt)
                    if source is None:
                        continue
                    if 'stage_events' in source and 'pull_events' in source:
                        violations.append(key)
    assert not violations, architecture_assertion_message('reguła testowana przez test_handler_does_not_stage_events_manually', 'warunek zapisany w asercji musi być spełniony', 'Handlers must NOT manually stage events via stage_events(agg.pull_events()).\nUse unit_of_work.save(Repo, aggregate) which pulls, maps and stages automatically:\n' + '\n'.join(violations))
