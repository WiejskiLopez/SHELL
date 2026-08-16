"""Koncept: reguła architektoniczna dotycząca process structure: test process handlers dont mutate aggregates.

Reguła: test sprawdza kontrakt architektoniczny process structure: test process handlers dont mutate aggregates.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files

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

def test_process_handlers_dont_mutate_aggregates() -> None:
    violations: list[str] = []
    for path in _iter_process_handler_files():
        rel = path.relative_to(BASE).as_posix()
        if rel in _PROCESS_HANDLER_MUTATION_KNOWN:
            continue
        content = path.read_text(encoding='utf-8')
        mutation_patterns = ['stage_events(', '.save(', '.commit(', 'append_event(', 'pull_events()']
        for pattern in mutation_patterns:
            if pattern in content:
                violations.append(f'{rel}: contains {pattern!r}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_process_handlers_dont_mutate_aggregates', 'warunek zapisany w asercji musi być spełniony', 'Process handlers must not directly mutate aggregates or UoW (no stage_events, save, commit, append_event, pull_events):\n' + '\n'.join(violations))
