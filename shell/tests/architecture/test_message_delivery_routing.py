"""Koncept: reguła architektoniczna — message nigdy nie jest broadcastem.

Reguła: konsument message (RabbitInboxConsumer podpięty pod bundle message delivery)
musi wiązać jawne, adresowane wzorce routingu (per odbiorca), nigdy goły ``#``.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń (dziś brak konsumenta
message — reguła blokuje błąd zanim pojawi się pierwszy producent).
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    parse_file,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


def _bootstrap_files() -> Iterator[Path]:
    for service_dir in sorted(BASE.glob("*_service")):
        bootstrap = service_dir / "bootstrap"
        if not bootstrap.is_dir():
            continue
        for py_file in bootstrap.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            yield py_file


def _keyword(node: ast.Call, name: str) -> ast.keyword | None:
    for keyword in node.keywords:
        if keyword.arg == name:
            return keyword
    return None


def test_message_consumer_binds_explicit_routing_keys() -> None:
    violations: list[str] = []
    for py_file in _bootstrap_files():
        tree = parse_file(py_file)
        if tree is None:
            continue
        rel = py_file.relative_to(BASE)
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call):
                continue
            if not _is_consumer_factory_call(call):
                continue
            models_keyword = _keyword(call, "models")
            if models_keyword is None:
                continue
            if not ast.unparse(models_keyword.value).endswith(".messages"):
                continue
            routing_keys_keyword = _keyword(call, "routing_keys")
            if routing_keys_keyword is None:
                violations.append(
                    f'{rel}: {call.lineno} — message consumer bez jawnych routing_keys (domyślny „#")'
                )
                continue
            keys = _constant_strings(routing_keys_keyword.value)
            if "#" in keys:
                violations.append(
                    f'{rel}: {call.lineno} — message consumer wiąże goły „#" zamiast adresowanego wzorca'
                )
    assert not violations, architecture_assertion_message(
        "message nigdy nie jest broadcastem",
        "message trafia wyłącznie do agregatu pracującego na treści; konsument wiąże adresowany wzorzec (np. message.<recipient_aggregate_name>.#)",
        violations,
    )


def _is_consumer_factory_call(call: ast.Call) -> bool:
    if not call.args:
        return False
    first = call.args[0]
    if not isinstance(first, ast.Name) or first.id != "RabbitInboxConsumer":
        return False
    if not isinstance(call.func, ast.Attribute):
        return False
    return call.func.attr == "Factory"


def _constant_strings(node: ast.AST) -> frozenset[str]:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        strings: set[str] = set()
        for element in node.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                strings.add(element.value)
        return frozenset(strings)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return frozenset({node.value})
    return frozenset()
