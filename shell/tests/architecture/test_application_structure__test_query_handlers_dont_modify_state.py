"""Koncept: reguła architektoniczna dotycząca application structure: test query handlers dont modify state.

Reguła: test sprawdza kontrakt architektoniczny application structure: test query handlers dont modify state.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files, parse_file

_KNOWN_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})
_KNOWN_QUERIES_NOT_FROZEN: frozenset[str] = frozenset({})

def test_query_handlers_dont_modify_state() -> None:
    violations: list[str] = []
    handler_dir = BASE / 'application' / 'query_handlers'
    if not handler_dir.exists():
        return
    for path in iter_py_files(handler_dir):
        tree = parse_file(path)
        if tree is None:
            continue
        content = path.read_text(encoding='utf-8')
        for keyword in ['stage_events', '.save(', '.commit(', 'append_event(', 'pull_events()']:
            if keyword in content:
                violations.append(f'{path.relative_to(BASE)}: contains {keyword!r}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_query_handlers_dont_modify_state', 'warunek zapisany w asercji musi być spełniony', 'Query handlers must NOT modify state (no stage_events, save, commit, append_event):\n' + '\n'.join(violations))
