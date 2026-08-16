"""Koncept: reguła architektoniczna dotycząca general conventions: test no comments in production code.

Reguła: test sprawdza kontrakt architektoniczny general conventions: test no comments in production code.

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


def test_no_comments_in_production_code() -> None:
    violations: list[str] = []
    _CHECK_LAYERS = frozenset({"domain", "application"})
    for layer in _CHECK_LAYERS:
        for path in iter_py_files(BASE / layer):
            rel = path.relative_to(BASE).as_posix()
            if rel in _COMMENT_KNOWN_EXCEPTIONS:
                continue
            content = path.read_text(encoding="utf-8")
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if (
                    stripped.startswith("#")
                    and "# noqa" not in stripped
                    and (not stripped.startswith("#!"))
                    and (not stripped.startswith("# -*-"))
                    and re.match("# \\w", stripped)
                ):
                    violations.append(f"{rel}:{i}: {stripped[:80]}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_no_comments_in_production_code",
        "warunek zapisany w asercji musi być spełniony",
        "Domain/application code should avoid comments (except # noqa):\n" + "\n".join(violations),
    )
