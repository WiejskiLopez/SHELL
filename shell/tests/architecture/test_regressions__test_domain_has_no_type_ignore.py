"""Koncept: reguła architektoniczna dotycząca regressions: test domain no type ignore.

Reguła: test sprawdza kontrakt architektoniczny regressions: test domain no type ignore.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import BASE, architecture_assertion_message, iter_domain_files


def test_domain_has_no_type_ignore() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        rel = path.relative_to(BASE).as_posix()
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "# type: ignore" in line:
                violations.append(f"{rel}:{line_no}: {line.strip()}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_domain_has_no_type_ignore",
        "warunek zapisany w asercji musi być spełniony",
        "Domain must not use `# type: ignore` — te same protokoły mają być możliwie typowalne:\n"
        + "\n".join(violations),
    )
