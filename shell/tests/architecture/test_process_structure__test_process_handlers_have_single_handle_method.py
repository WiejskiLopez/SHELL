"""Koncept: reguła architektoniczna dotycząca process structure: test process handlers have single handle method.

Reguła: test sprawdza kontrakt architektoniczny process structure: test process handlers have single handle method.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_py_files,
    parse_file,
    public_method_names,
)

if TYPE_CHECKING:
    from pathlib import Path
_PROCESS_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})

def _iter_process_handler_files() -> list[Path]:
    files = []
    for handler_dir in (BASE / 'process').rglob('handlers'):
        if handler_dir.is_dir():
            for path in iter_py_files(handler_dir):
                files.append(path)
    return files
_PROCESS_HANDLER_MUTATION_KNOWN: frozenset[str] = frozenset({})

def test_process_handlers_have_single_handle_method() -> None:
    violations: list[str] = []
    for path in _iter_process_handler_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not node.name.endswith('Handler'):
                continue
            pub_methods = public_method_names(node)
            handle_methods = [m for m in pub_methods if m == 'handle']
            if len(handle_methods) != 1:
                key = f'{path.relative_to(BASE)}: class {node.name}'
                if key not in _PROCESS_HANDLER_EXCEPTIONS:
                    violations.append(key)
    assert not violations, architecture_assertion_message('reguła testowana przez test_process_handlers_have_single_handle_method', 'warunek zapisany w asercji musi być spełniony', 'Process handlers must have exactly one public method named `handle`:\n' + '\n'.join(violations))
