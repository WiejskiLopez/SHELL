# Porty domenowe (RepositoryPort, IdGenerator, Clock, Logger)

## Cel / Co realizuje

Porty domenowe w `shell/platform/domain/ports/` definiują minimalne kontrakty (protocols) między warstwą domeny a adapterami infrastruktury: `RepositoryPort` (operacje CRUD na agregatach), `IdGenerator` (generowanie identyfikatorów), `Clock` (źródło czasu). Port `Logger` żyje w warstwie aplikacji (`shell/platform/application/ports/logger.py`). Dzięki nim warstwa domeny nie zależy od konkretnych implementacji (baza danych, UUID, `datetime`, logger).

## Problem

W architekturze hexagonalnej domena nie może importować infrastruktury, ale potrzebuje zewnętrznych usług: repozytoriów, generatorów ID, czasu i logowania. Rozwiązaniem są odwrócone zależności: domena definiuje interfejs (port), infrastruktura dostarcza implementację (adapter) wstrzykiwaną przez composition root. Porty muszą być minimalne, by nie wyciekać do domeny szczegółów technicznych (SQL, frameworki).

## Realizacja techniczna

### RepositoryPort — `shell/platform/domain/ports/repository_port.py`

```python
TAggregate = TypeVar("TAggregate")
TId = TypeVar("TId", contravariant=True)

class RepositoryPort(Protocol[TAggregate, TId]):
    async def get_by_id(self, id: TId) -> TAggregate | None: ...

    async def save(self, entity: TAggregate) -> None: ...

    async def delete(self, id: TId) -> None: ...

    async def exists(self, id: TId) -> ExistsResult: ...
```

- Generyczny, minimalny protocol; każdy repozytorium agregatu rozszerza ten protocol, aby zagwarantować cztery kanoniczne operacje.
- `get_by_id(id: TId) -> TAggregate | None` — zwraca `None` gdy agregat nie istnieje (brak wyjątku).
- `save(entity: TAggregate) -> None` — zapis (pełni też rolę update).
- `delete(id: TId) -> None` — usunięcie (soft delete na poziomie agregatu).
- `exists(id: TId) -> ExistsResult` — zwraca `ExistsResult` (frozen dataclass z `value: bool` i `__bool__`), nie goły `bool`.
- Wszystkie metody są `async`. `TId` jest kontrawariantny (`TypeVar("TId", contravariant=True)`).
- `TAggregate`/`TId` są niesparametryzowane boundami — tożsamość agregatu jest nieprzezroczysta.

### IdGenerator — `shell/platform/domain/ports/identity.py`

```python
TId = TypeVar("TId", bound=EntityId)

class IdGenerator(Protocol):
    def new_id(self, id_type: type[TId]) -> TId: ...
```

- `new_id(id_type: type[TId]) -> TId` — zwraca nowy identyfikator konkretnego typu pochodnego `EntityId`.
- Bound `TId, bound=EntityId` wymusza, że generowane identyfikatory są zawsze value objects dziedziczące po `EntityId` (patrz [entity-id](entity-id.md)).

### Clock — `shell/platform/domain/ports/time.py`

```python
class Clock(Protocol):
    def now(self) -> datetime: ...
```

- Abstrakcyjne źródło czasu; adaptery dostarczają czas rzeczywisty (UTC) lub zamrożony do testów.
- Używany do tworzenia `OccurredAt`, `DeletedAt`, `Timestamp` (timezone-aware UTC).

### Logger — `shell/platform/application/ports/logger.py`

```python
class Logger(Protocol):
    def debug(self, msg: str, **kw: object) -> None: ...
    def info(self, msg: str, **kw: object) -> None: ...
    def warning(self, msg: str, **kw: object) -> None: ...
    def error(self, msg: str, **kw: object) -> None: ...
```

- Cztery poziomy logowania; `**kw` przenosi pola strukturalne (np. `correlation_id`).
- Wstrzykiwany do klas domenowych/aplikacyjnych zamiast bezpośredniego `import logging`.

Wszystkie porty to strukturalne `Protocol` (duck typing) — adapter nie musi dziedziczyć, wystarczy że ma zgodny kształt metod. Implementacje żyją w `shell/platform/infrastructure/` (np. persistence, serializacja UUID, konfiguracja loggera).

## Kluczowe pliki

- `shell/platform/domain/ports/repository_port.py`
- `shell/platform/domain/ports/identity.py`
- `shell/platform/domain/ports/time.py`
- `shell/platform/application/ports/logger.py`
- `shell/platform/domain/value_objects/exists_result.py`

## Powiązane koncepcje

- [ports-and-adapters](ports-and-adapters.md)
- [aggregate-root](aggregate-root.md)
- [entity-id](entity-id.md)
- [sqlalchemy-persistence](sqlalchemy-persistence.md)
- [architecture-overview](architecture-overview.md)
