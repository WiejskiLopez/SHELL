"""Koncept: reguła architektoniczna dotycząca bc isolation: test cross bc http adapters use httpx not sql.

Reguła: test sprawdza kontrakt architektoniczny bc isolation: test cross bc http adapters use httpx not sql.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    get_imports,
    iter_layer_dirs,
    iter_py_files,
)

if TYPE_CHECKING:
    import pathlib


def test_cross_bc_http_adapters_use_httpx_not_sql() -> None:
    """All cross-BC HTTP adapter files must import httpx and must NOT
    import persistence.sql or domain repositories from other BCs."""
    http_adapter_dirs: list[pathlib.Path] = list(
        iter_layer_dirs(
            "infrastructure", "execution", "graph_execution", "adapters", "graph_definition"
        )
    )
    http_adapter_dirs.extend(
        iter_layer_dirs(
            "infrastructure",
            "execution",
            "session_execution",
            "adapters",
            "session_query_provider",
        )
    )
    http_adapter_dirs.extend(iter_layer_dirs("infrastructure", "user", "user", "http"))
    http_adapter_dirs.extend(iter_layer_dirs("infrastructure", "project", "http"))
    violations: list[str] = []
    for adapter_dir in http_adapter_dirs:
        if not adapter_dir.exists():
            continue
        for path in iter_py_files(adapter_dir):
            if "_http_adapter" not in path.name:
                continue
            rel = path.relative_to(BASE).as_posix()
            imports = get_imports(path)
            if not any("httpx" in imp for imp in imports):
                violations.append(f"{rel}: missing httpx import")
            for imp in imports:
                if "persistence.sql" in imp:
                    violations.append(f"{rel}: imports SQL persistence {imp!r}")
                if ".repositories." in imp:
                    violations.append(f"{rel}: imports repositories {imp!r}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_cross_bc_http_adapters_use_httpx_not_sql",
        "warunek zapisany w asercji musi być spełniony",
        "Cross-BC HTTP adapters must use httpx, not SQL/repositories:\n" + "\n".join(violations),
    )
