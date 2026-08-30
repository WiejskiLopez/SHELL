"""Koncept: reguła architektoniczna dotycząca regressions: test framework does not fake 501 on DI failure.

Reguła: test sprawdza kontrakt architektoniczny regressions: test framework does not fake 501 on DI failure.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import re

from _arch_helpers import BASE, architecture_assertion_message, iter_layer_files

# Wzorzec: szeroki `except Exception` natychmiast zamieniany na HTTP 501 bez logu
_BLOCKER = re.compile(
    r"except\s+Exception\s*:.*?status_code\s*=\s*501",
    flags=re.DOTALL,
)


def test_framework_does_not_fake_501_on_di_failure() -> None:
    violations: list[str] = []
    for path in iter_layer_files("framework"):
        rel = path.relative_to(BASE).as_posix()
        if "api" not in path.parts and "cli" not in path.parts:
            continue
        src = path.read_text(encoding="utf-8")
        if _BLOCKER.search(src):
            violations.append(f"{rel}: except Exception -> HTTPException(501) bez logu")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_framework_does_not_fake_501_on_di_failure",
        "warunek zapisany w asercji musi być spełniony",
        "Framework nie może maskować błędu DI jako HTTP 501 — użyj Depends(get_query_bus)/propaguj i loguj:\n"
        + "\n".join(violations),
    )
