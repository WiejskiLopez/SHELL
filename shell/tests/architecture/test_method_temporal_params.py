"""Koncept: reguła architektoniczna dotycząca method temporal params.

Reguła: test sprawdza kontrakt architektoniczny method temporal params.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    AGGREGATE_BASES,
    BASE,
    architecture_assertion_message,
    architecture_failure,
    extends_any_base,
    find_classes,
    iter_domain_files,
    parse_file,
)

_DOMAIN_METHODS = frozenset({"__init__", "create", "restore", "_new", "_change", "_delete"})
_ENTITY_OR_AGGREGATE = AGGREGATE_BASES | {"Entity"}
_TEMPORAL_PARAM_NAMES = frozenset({"created_at", "occurred_at", "changed_at", "deleted_at", "now"})


def _all_param_names(statement: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    return [
        parameter.arg
        for parameter in (
            *statement.args.posonlyargs,
            *statement.args.args,
            *statement.args.kwonlyargs,
        )
        if parameter.arg not in {"self", "cls"}
    ]


def test_method_params_temporal_first() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, _ENTITY_OR_AGGREGATE):
                continue
            for statement in node.body:
                if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if statement.name not in _DOMAIN_METHODS:
                    continue
                parameters = _all_param_names(statement)
                non_id = [parameter for parameter in parameters if parameter not in {"id", "id_"}]
                temporal = [parameter for parameter in non_id if parameter in _TEMPORAL_PARAM_NAMES]
                business = [
                    parameter for parameter in non_id if parameter not in _TEMPORAL_PARAM_NAMES
                ]
                if (
                    temporal
                    and business
                    and (
                        max(parameters.index(value) for value in temporal)
                        > min(parameters.index(value) for value in business)
                    )
                ):
                    violations.append(
                        f"{path.relative_to(BASE)}:{statement.lineno} {node.name}.{statement.name}: {parameters}"
                    )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_method_params_temporal_first",
        "warunek zapisany w asercji musi być spełniony",
        architecture_failure(
            "czasowe parametry metod domenowych poprzedzają parametry biznesowe",
            "id/id_ mogą być pierwsze, następnie created/occurred/changed/deleted/now i wartości biznesowe",
            violations,
            "zmień kolejność parametrów metod, zachowując ich nazwy",
        ),
    )
