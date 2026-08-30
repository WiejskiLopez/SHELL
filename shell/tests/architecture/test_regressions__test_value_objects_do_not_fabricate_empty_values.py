"""Koncept: reguła architektoniczna dotycząca regressions: test value objects reject empty fallback.

Reguła: test sprawdza kontrakt architektoniczny regressions: test value objects reject empty fallback.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import re

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    iter_named_dirs,
    iter_py_files,
)

_EMPTY_FACTORY = re.compile(r"def\s+empty\s*\(|return\s+cls\(\s*[\"']\s*[\"']\s*\)")


def test_value_objects_do_not_fabricate_empty_values() -> None:
    violations: list[str] = []
    for vo_dir in iter_named_dirs("domain", "value_objects"):
        for path in iter_py_files(vo_dir):
            rel = path.relative_to(BASE).as_posix()
            src = path.read_text(encoding="utf-8")
            for line_no, line in enumerate(src.splitlines(), 1):
                if _EMPTY_FACTORY.search(line):
                    violations.append(f"{rel}:{line_no}: {line.strip()}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_value_objects_do_not_fabricate_empty_values",
        "warunek zapisany w asercji musi być spełniony",
        "ValueObject nie może tworzyć pustej wartości jako fallback (no-empty-fallbacks):\n"
        + "\n".join(violations),
    )
