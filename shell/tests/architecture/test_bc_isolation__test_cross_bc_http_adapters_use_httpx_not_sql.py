"""Koncept: reguła architektoniczna dotycząca bc isolation: test cross bc http adapters use httpx not sql.

Reguła: test sprawdza kontrakt architektoniczny bc isolation: test cross bc http adapters use httpx not sql.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from _arch_helpers import BASE, architecture_assertion_message, get_imports, iter_py_files

if TYPE_CHECKING:
    import pathlib
_BCS = frozenset({'execution_service', 'definition_service', 'session_service', 'user_service', 'project_service', 'scheduling_service', 'ingestion_service'})
_ALLOWED_CROSS_BC = frozenset({'shell.platform.domain', 'shell.platform.application', 'shell.user_service.application.user.user.integration_events', 'shell.user_service.application.user.auth_session.integration_events'})

def _is_cross_bc_import(imp: str, source_bc: str) -> str | None:
    """If imp crosses a BC boundary (is not platform), return the target BC name."""
    for bc in _BCS:
        if bc == source_bc or bc == 'platform':
            continue
        prefixes = (f'shell.domain.{bc}', f'shell.application.{bc}', f'shell.{bc}.domain.{bc}', f'shell.{bc}.application.{bc}', f'shell.{bc}.')
        if imp.startswith(prefixes):
            return bc
    return None

def _is_allowed_cross_bc(imp: str) -> bool:
    return any(imp == allowed or imp.startswith(allowed + '.') for allowed in _ALLOWED_CROSS_BC)
_CROSS_BC_KNOWN_VIOLATIONS: list[str] = []

def _bc_source_path(bc: str) -> pathlib.Path:
    """Return the source tree owned by a bounded context."""
    return BASE / bc

def _cross_bc_violations() -> list[str]:
    violations: list[str] = []
    for source_bc in _BCS:
        source_path = _bc_source_path(source_bc)
        if not source_path.exists():
            continue
        for path in iter_py_files(source_path):
            for imp in get_imports(path):
                target_bc = _is_cross_bc_import(imp, source_bc)
                if target_bc is None or _is_allowed_cross_bc(imp):
                    continue
                key = f'{path.relative_to(BASE).as_posix()}: imports {imp!r} (from BC {target_bc})'
                if not any(key.startswith(k) for k in _CROSS_BC_KNOWN_VIOLATIONS):
                    violations.append(key)
    return violations

def test_cross_bc_http_adapters_use_httpx_not_sql() -> None:
    """All cross-BC HTTP adapter files must import httpx and must NOT
    import persistence.sql or domain repositories from other BCs."""
    http_adapter_dirs = [BASE / 'infrastructure' / 'execution' / 'http', BASE / 'user' / 'infrastructure' / 'user' / 'http', BASE / 'infrastructure' / 'project' / 'http']
    violations: list[str] = []
    for adapter_dir in http_adapter_dirs:
        if not adapter_dir.exists():
            continue
        for path in iter_py_files(adapter_dir):
            rel = path.relative_to(BASE).as_posix()
            imports = get_imports(path)
            if not any('httpx' in imp for imp in imports):
                violations.append(f'{rel}: missing httpx import')
            for imp in imports:
                if 'persistence.sql' in imp:
                    violations.append(f'{rel}: imports SQL persistence {imp!r}')
                if '.repositories.' in imp:
                    violations.append(f'{rel}: imports repositories {imp!r}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_cross_bc_http_adapters_use_httpx_not_sql', 'warunek zapisany w asercji musi być spełniony', 'Cross-BC HTTP adapters must use httpx, not SQL/repositories:\n' + '\n'.join(violations))
