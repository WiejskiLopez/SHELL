"""Koncept: brak zahardkodowanych sekretów produkcyjnych.

Reguła: produkcyjna konfiguracja pobiera sekrety ze środowiska lub secret managera.

Poprawnie: produkcyjne pliki nie zawierają używalnych loginów, haseł ani tokenów.
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).parents[3]
_PRODUCTION_FILES = (
    _ROOT / ".env.prod.example",
    _ROOT / "shell" / "rabbitmq" / "docker" / "docker-compose.yml",
    _ROOT / "shell" / "platform" / "infrastructure" / "configuration" / "shell_config.py",
)
_REAL_CREDENTIAL = re.compile(
    r"(?:shell:shell|dev-user-key|change-me|super-secret|"
    r"amqp://[^\s:/]+:[^\s@]+@(?!(?:replace-host|localhost)(?::|/)))",
    re.IGNORECASE,
)


def test_production_files_do_not_contain_hardcoded_credentials() -> None:
    violations: list[str] = []
    for path in _PRODUCTION_FILES:
        text = path.read_text(encoding="utf-8")
        if _REAL_CREDENTIAL.search(text):
            violations.append(path.relative_to(_ROOT).as_posix())
    assert not violations, "Hardcoded production credentials found: " + ", ".join(violations)
