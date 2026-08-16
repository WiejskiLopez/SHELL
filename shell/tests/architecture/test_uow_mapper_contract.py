"""Koncept: reguła architektoniczna dotycząca uow mapper contract.

Reguła: test sprawdza kontrakt architektoniczny uow mapper contract.

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

_UOW_BASES = tuple(BASE.glob('*_service/infrastructure'))
_KNOWN_NON_UOW_EXTENDERS: frozenset[str] = frozenset()

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
                        has_mapper_param = any(arg.arg == 'mapper' for arg in stmt.args.args)
                        for node_in_init in ast.walk(stmt):
                            if isinstance(node_in_init, ast.Call) and isinstance(node_in_init.func, ast.Attribute) and (node_in_init.func.attr == '__init__'):
                                passes_mapper |= any(kw.arg == 'mapper' for kw in node_in_init.keywords)
                if not has_mapper_param:
                    violations.append(f'{key}: brak parametru mapper w __init__')
                elif not passes_mapper:
                    violations.append(f'{key}: mapper nie jest przekazany do super().__init__')
    assert not violations, architecture_assertion_message('reguła testowana przez test_per_bc_uow_accepts_mapper', 'warunek zapisany w asercji musi być spełniony', 'Naruszona reguła: UoW musi przyjmować i przekazywać mapper.\nZnaleziono:\n' + '\n'.join(violations) + '\nJak naprawić: dodaj mapper=mapper do konstruktora bazowego UoW.')
