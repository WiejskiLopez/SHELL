"""Koncept: reguła architektoniczna dotycząca general conventions: test noqa has justification.

Reguła: test sprawdza kontrakt architektoniczny general conventions: test noqa has justification.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import re

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files

_KNOWN_MISSING_FUTURE: frozenset[str] = frozenset({})
_PATHS_WITHOUT_TYPE_HINTS: frozenset[str] = frozenset({})
_KNOWN_INIT_DEFINITIONS: frozenset[str] = frozenset({})
_NOQA_KNOWN_INVALID: frozenset[str] = frozenset({})
_NOQA_KNOWN_WITHOUT_REASON: frozenset[str] = frozenset({})
_COMMENT_KNOWN_EXCEPTIONS: frozenset[str] = frozenset({})

def test_noqa_has_justification() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel in _NOQA_KNOWN_INVALID or rel.startswith('tests/architecture/'):
            continue
        if rel.startswith('.venv/'):
            continue
        content = path.read_text(encoding='utf-8')
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if '# noqa' in stripped:
                has_code = bool(re.search('# noqa:\\s*\\w+', stripped))
                has_reason = bool(re.search('(--|—|–|-)', stripped))
                if not has_code or not has_reason:
                    key = f'{rel}:{i}'
                    if key not in _NOQA_KNOWN_WITHOUT_REASON:
                        violations.append(f'{rel}:{i}: {stripped}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_noqa_has_justification', 'warunek zapisany w asercji musi być spełniony', 'Each # noqa must include rule code and justification (-- reason):\n' + '\n'.join(violations))
