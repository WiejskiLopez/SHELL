"""ContractCatalog — explicit registry of public cross-BC contracts per bounded context.

The catalog is the single source of truth for which event/message/command types a
bounded context publicly exposes or consumes. It records owner, producer(s) and
consumer(s) plus the supported schema versions, so the deserialization registry is
never the only authority on a contract's existence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class ContractEntry:
    type_name: str
    owner: str
    supported_schema_versions: frozenset[int] = frozenset({1})
    producers: tuple[str, ...] = ()
    consumers: tuple[str, ...] = ()
    retry_policy: str = "default"


@dataclass(frozen=True, slots=True)
class ContractCatalog:
    owner: str
    entries: tuple[ContractEntry, ...]

    def names(self) -> set[str]:
        return {entry.type_name for entry in self.entries}

    def by_name(self, type_name: str) -> ContractEntry | None:
        for entry in self.entries:
            if entry.type_name == type_name:
                return entry
        return None

    def assert_covers(self, registered: Iterable[str]) -> None:
        """Raise if any registered type has no catalog entry."""
        registered_set = set(registered)
        missing = registered_set - self.names()
        if missing:
            raise ValueError(
                f"Contract catalog of {self.owner} is missing entries for: "
                + ", ".join(sorted(missing))
            )


def build_contract_catalog(
    owner: str,
    entries: Iterable[ContractEntry],
) -> ContractCatalog:
    return ContractCatalog(owner=owner, entries=tuple(entries))


def build_contract_catalog_from_registry(
    owner: str,
    registry: Mapping[str, object],
    *,
    extra_consumed: Mapping[str, tuple[str, ...]] | None = None,
) -> ContractCatalog:
    """Build a catalog from a BC event registry.

    Each registered type becomes a ``ContractEntry`` owned by ``owner`` (produced
    by the owning BC). Types the BC additionally consumes from other BCs can be
    listed in ``extra_consumed`` with the consuming BC as the key's value.

    ``extra_consumed`` types must already be present in ``registry`` (they are
    registered by the BC's event registry as explicitly consumed contracts).
    """
    consumed = dict(extra_consumed or {})
    entries = [
        ContractEntry(
            type_name=type_name,
            owner=owner,
            producers=(owner,),
            consumers=consumed.get(type_name, ()),
        )
        for type_name in registry
    ]
    return ContractCatalog(owner=owner, entries=tuple(entries))
