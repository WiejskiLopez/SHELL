"""Koncept: reguła architektoniczna dotycząca slot temporal order.

Reguła: test sprawdza kontrakt architektoniczny slot temporal order.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    AGGREGATE_BASES,
    BASE,
    architecture_assertion_message,
    architecture_failure,
    extends_any_base,
    find_classes,
    get_slots,
    has_slots,
    iter_domain_files,
    parse_file,
)

_TEMPORAL_ORDER = ("_created_at", "_occurred_at", "_changed_at", "_deleted_at")
_ENTITY_OR_AGGREGATE = AGGREGATE_BASES | {"Entity"}
_KNOWN_SLOT_ORDER_VIOLATIONS: frozenset[str] = frozenset({})


def _temporal_rank(field: str) -> int:
    try:
        return _TEMPORAL_ORDER.index(field)
    except ValueError:
        return -1


def test_slots_temporal_fields_first() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, _ENTITY_OR_AGGREGATE) or not has_slots(node):
                continue
            slots = get_slots(node)
            temporal = [slot for slot in slots if _temporal_rank(slot) >= 0]
            business = [slot for slot in slots if _temporal_rank(slot) < 0]
            if (
                temporal
                and business
                and (
                    max(slots.index(slot) for slot in temporal)
                    > min(slots.index(slot) for slot in business)
                )
            ):
                violations.append(
                    f"{path.relative_to(BASE)}:{node.lineno} {node.name}: business slots precede temporal slots: {slots}"
                )
            ranked = [_temporal_rank(slot) for slot in temporal]
            if ranked != sorted(ranked):
                violations.append(
                    f"{path.relative_to(BASE)}:{node.lineno} {node.name}: temporal slots are out of order: {temporal}"
                )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_slots_temporal_fields_first",
        "warunek zapisany w asercji musi być spełniony",
        architecture_failure(
            "czasowe pola są przed polami biznesowymi w slots agregatu",
            "_created_at/_occurred_at poprzedzają _changed_at, potem _deleted_at i pola biznesowe",
            violations,
            "zmień kolejność deklaracji __slots__ agregatu",
        ),
    )
