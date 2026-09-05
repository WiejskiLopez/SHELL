# Contract Catalog

## Cel / Co realizuje

Implementuje jawny, per-bounded-context rejestr kontraktów publicznych
(`ContractCatalog`/`ContractEntry`) — pojedyncze źródło prawdy o tym, które
typy event/command dany BC produkuje lub konsumuje. Katalog odnotowuje
właściciela, producentów, konsumentów oraz wspierane wersje schematu, dzięki
czemu rejestr deserializacji nie jest jedynym autorytetem w kwestii istnienia
danego kontraktu.

## Problem

W integracji między BC brakuje jawności: kontrakt "istnieje", bo jest w
rejestrze typów do deserializacji — ale nikt nie deklaruje, kto jest jego
właścicielem, kto go produkuje, a kto konsumuje. Powoduje to
niedeterministyczne zależności, brak kontroli nad przestarzałymi kontraktami i
trudność w wyłapaniu kontraktu, który został zarejestrowany, ale nigdy nie
został jawnie zaakceptowany przez dany BC.

## Realizacja techniczna

### Typy — `shell/platform/application/contracts/contract_catalog.py`

- `ContractEntry` — `@dataclass(frozen=True, slots=True)`:
  - `type_name: str` — nazwa typu kontraktu;
  - `owner: str` — właściciel kontraktu;
  - `supported_schema_versions: frozenset[int] = frozenset({1})`;
  - `producers: tuple[str, ...] = ()`;
  - `consumers: tuple[str, ...] = ()`;
  - `retry_policy: str = "default"`.
- `ContractCatalog` — `@dataclass(frozen=True, slots=True)` z polami
  `owner: str` i `entries: tuple[ContractEntry, ...]` oraz metodami:
  - `names() -> set[str]` — zbiór `type_name` wszystkich wpisów;
  - `by_name(type_name) -> ContractEntry | None` — wyszukiwanie liniowe;
  - `assert_covers(registered: Iterable[str])` — podnosi `ValueError`, gdy
    jakikolwiek zarejestrowany typ nie ma wpisu w katalogu:
    `f"Contract catalog of {self.owner} is missing entries for: ..."`.

### Fabryki

- `build_contract_catalog(owner, entries) -> ContractCatalog` — buduje katalog z
  jawnie przekazanych `ContractEntry` (krotka konwertowana do `tuple`).
- `build_contract_catalog_from_registry(owner, registry, *, extra_consumed=None)`
  — buduje katalog z rejestru eventów BC (`registry: Mapping[str, object]`):
  - każdy zarejestrowany typ staje się `ContractEntry(type_name=..., owner=owner,
    producers=(owner,), consumers=consumed.get(type_name, ()))`;
  - typy dodatkowo konsumowane z innych BC podaje się w `extra_consumed`
    (`Mapping[str, tuple[str, ...]]`, klucz = typ, wartość = BC konsumujące);
    typy z `extra_consumed` muszą już być obecne w `registry` (są rejestrowane
    przez rejestr eventów BC jako jawnie konsumowane kontrakty).

### Zastosowanie

Katalog jest budowany przy starcie BC (composition root / rejestracja DI) i
używany m.in. do walidacji spójności: `assert_covers(...)` z zestawem typów
zarejestrowanych do deserializacji gwarantuje, że każdy kontrakt jest jawnie
zaakceptowany w katalogu danego BC. Wspiera też wersjonowanie schematu przez
`supported_schema_versions` (powiązane z wersjonowaniem envelope).

## Kluczowe pliki

- `shell/platform/application/contracts/contract_catalog.py`

## Powiązane koncepcje

- [integration-contracts](integration-contracts.md)
- [envelope-versioning](envelope-versioning.md)
- [delivery-models](delivery-models.md)
- [contracts] — patrz [integration-mapper](integration-mapper.md)
- [architecture-overview](architecture-overview.md)
