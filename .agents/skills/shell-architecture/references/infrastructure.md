# Warstwa infrastruktury

`infrastructure/` implementuje porty zdefiniowane w `domain/` i `application/`. Tu żyją SQLAlchemy, InMemory adapters, outbox, migracje.

## Port-to-Adapter inheritance (KRYTYCZNE)

Każdy adapter infrastrukturalny (SQL + InMemory) jawnie implementuje port domenowy przez dziedziczenie:

```python
# DOMAIN PORT
class WorkflowRepository(Protocol):
    async def get_by_id(self, id: WorkflowId) -> Workflow | None: ...
    async def get_by_task_execution_id(self, task_execution_id: TaskExecutionId) -> Workflow | None: ...

# SQL ADAPTER — jawna implementacja
class SqlWorkflowRepository(WorkflowRepository):
    ...

# INMEMORY ADAPTER — jawna implementacja
class InMemoryWorkflowRepository(WorkflowRepository):
    ...
```

Dlaczego to ma znaczenie:
- **Symetria między SQL i InMemory** — oba implementują ten sam kontrakt
- Type-checking — mypy wychwyci brakującą metodę w adapterze
- Runtime safety — `isinstance` działa poprawnie (jeśli Protocol `@runtime_checkable`)

Jeśli metoda portu jest zbyt trudna do zaimplementowania w InMemory, to znaczy że port jest źle zaprojektowany (ujawnia detal persystencji), a nie że InMemory ma zwracać `None`/no-op. No-op stub w InMemory maskuje błędy w testach jednostkowych — one ujawnią się dopiero na SQL, gdy będzie za późno.

## SQL Repositories

- Implementują porty z `domain/repositories/` przez jawne dziedziczenie
- W `infrastructure/persistence/sql/repositories/`
- Używają SQLAlchemy 2.0 async ORM
- Dialekt wybierany runtime'm przez `database_url` — jeden zestaw modeli i repozytoriów dla SQLite i PostgreSQL
- Mapowanie ORM → Domain w `infrastructure/persistence/sql/mappers/` (nie w repozytorium)
- Nigdy nie importują domain entity w runtime — zawsze pod `TYPE_CHECKING` + mapper
- Każda operacja w kontekście `UnitOfWork` — nigdy samodzielnego zarządzania sesją
- Konwencja nazewnictwa: `get_by_id()`, `save()`, `delete()`, `list_by_*()`, `get_latest_by_*()`

## Mapper symmetry (KRYTYCZNE)

Każdy mapper musi być symetryczny (round-trip): `entity → model → entity` musi zachować wszystkie dane. Każde pole agregatu, które trafia do bazy, musi mieć:

1. kolumnę w modelu ORM,
2. odczyt w `*_model_to_entity`,
3. zapis w `*_entity_to_model`.

Brak ktoregokolwiek z trzech = pole tracone przy reloadzie z bazy. Bo contowność agregatu (np. liczniki pętli, zbiory oczekujących nodów) jest resetowana — efekty od nieskończonej pętli po deadlock.

## InMemory Repositories

- W `infrastructure/persistence/memory/`
- Używane wyłącznie w testach jednostkowych
- Implementują te same porty co SQL odpowiedniki przez jawne dziedziczenie
- Przechowują dane w słownikach w pamięci
- Nigdy nie dodają metod których nie ma w porcie domenowym
- Filtrowanie (po `is_current`, `workflow_id` itp.) musi być identyczne jak w SQL — InMemory ma odwzorowywać semantykę SQL, nie uproszczoną wersję

## ORM Models (SQLAlchemy)

- W `infrastructure/persistence/sql/models/`
- Anemiczne — wyłącznie mapa tabel, nigdy logiki biznesowej
- Oddzielny model dla każdego agregatu/encji
- Relacje tam gdzie potrzebne, ale bez kaskadowego ładowania przez `selectin` (chyba że wymagane przez kontrakt)
- Kolumny JSON dla elastycznych struktur

## Migracje (Alembic) — lockstep z modelem (KRYTYCZNE)

- W `infrastructure/persistence/migrations/sql/versions/`
- Downgrade zawsze obsłużony
- Dialekt-specific DDL przez `op.get_context().dialect.name`

Każda zmiana modelu ORM (dodanie/usunięcie kolumny, zmiana typu, zmiana indeksu/constraint) **wymaga migracji**. Model i schemat bazy muszą być w pełnej zgodności — bez migracji `alembic upgrade head` na istniejącej bazie skończy się `OperationalError: no such column`.

Zasada inwersyjna: jeśli nowa migracja dodaje kolumnę, której model ORM nie ma (lub odwrotnie), jest to sygnał, że refaktoryzacja nie została domknięta.

## Outbox / Messaging

- Transactional Outbox: zapis eventu w tej samej transakcji co domena
- `outbox_event` tabela → `OutboxRelay` → EventPublisher
- Gwarancja at-least-once delivery
- Kompozytowy EventPublisher składa wiele publisherów (log, SQL, audit)
- Event registry nie używa hardcoded mapy string → klasa. Automatyczna rejestracja przez `__init_subclass__` w base class.
