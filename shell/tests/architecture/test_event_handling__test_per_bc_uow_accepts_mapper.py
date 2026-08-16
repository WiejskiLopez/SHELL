"""Koncept: reguła architektoniczna dotycząca event handling: test per bc uow accepts mapper.

Reguła: test sprawdza kontrakt architektoniczny event handling: test per bc uow accepts mapper.

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

def test_per_bc_uow_accepts_mapper() -> None:
    violations: list[str] = []
    for uow_base in _UOW_BASES:
        for py_file in iter_py_files(uow_base):
            if py_file.name != 'unit_of_work.py':
                continue
            rel = py_file.relative_to(BASE)
            tree = parse_file(py_file)
            if tree is None:
                continue
            for class_node in find_classes(tree):
                bases = {b.id for b in class_node.bases if isinstance(b, ast.Name)}
                if 'SqlAlchemyUnitOfWorkBase' not in bases:
                    continue
                key = f'{rel}: class {class_node.name}'
                if key in _KNOWN_NON_UOW_EXTENDERS:
                    continue
                has_mapper_param = False
                passes_mapper = False
                for stmt in class_node.body:
                    if isinstance(stmt, ast.FunctionDef) and stmt.name == '__init__':
                        for arg in stmt.args.args:
                            if arg.arg == 'mapper':
                                has_mapper_param = True
                        for node_in_init in ast.walk(stmt):
                            if isinstance(node_in_init, ast.Call):
                                func = node_in_init.func
                                if isinstance(func, ast.Attribute) and func.attr == '__init__':
                                    for kw in node_in_init.keywords:
                                        if kw.arg == 'mapper':
                                            passes_mapper = True
                if not has_mapper_param:
                    violations.append(f'{key}: __init__ missing mapper parameter')
                elif not passes_mapper:
                    violations.append(f'{key}: __init__ does not forward mapper to super().__init__')
    assert not violations, architecture_assertion_message('reguła testowana przez test_per_bc_uow_accepts_mapper', 'warunek zapisany w asercji musi być spełniony', 'All SqlAlchemyUnitOfWorkBase subclasses must accept a mapper parameter and forward it to super().__init__():\n' + '\n'.join(violations))
