# Warstwa aplikacyjna

`application/` orkiestruje przypadki użycia: pobiera agregaty z repozytoriów, wywołuje metody domenowe, persystuje wynik. Nie zawiera reguł biznesowych.

## CQRS — Command / Query Separation

- **Commands** zmieniają stan, zwracają `None` lub ID utworzonego obiektu
- **Queries** nie zmieniają stanu, zwracają DTO
- Każda komenda/kwerenda w osobnej klasie w `application/commands/` lub `application/queries/`
- Każdy handler w osobnej klasie w `application/command_handlers/` lub `application/query_handlers/`
- Handler spełnia kontrakt: `handle(command: TCommand) -> Any`

### Command / Query / Event Bus
- `CommandBus` → rejestracja `command_type → handler_factory`
- `QueryBus` → rejestracja `query_type → handler_factory`
- `EventBus` → rejestracja `event_type → handler_factory` (1:N — jeden event może mieć wielu subskrybentów)
- Bus jest tylko dispatcherem — nie zawiera logiki biznesowej
- Busy konfigurowane w `bootstrap/`

## Unit of Work (UoW) — wzorzec transakcyjny

`UnitOfWork` jest zawsze async context managerem. Wzorzec w handlerze:

```python
async def handle(self, command: SomeCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        aggregate = await unit_of_work.some_repo.get_by_id(command.some_id)
        aggregate.do_something()                      # append_event() wewnątrz
        unit_of_work.stage_events(aggregate.pull_events())     # OBOWIĄZKOWE
    # commit() przez __aexit__
```

Zasady:
- `commit()` na `__aexit__` jeśli brak wyjątku; `rollback()` jeśli wyjątek
- Nigdy ręcznego `uow.commit()` w handlerze
- Po każdej mutacji agregatu wołaj `uow.stage_events(aggregate.pull_events())`
- Outbox zapisywany w tej samej transakcji co zmiany domenowe
- Idempotencja handlerów: wielokrotne wykonanie tego samego eventu/komendy nie zmienia stanu

### Two-phase UoW — dla długotrwałych operacji

Gdy między pobraniem agregatu a zapisem wyniku jest długotrwała operacja zewnętrzna (np. `GraphNodeExecutionProcessRunner.run()`), nie trzymaj otwartej transakcji na ten czas. Użyj dwóch osobnych bloków:

```python
async def handle(self, command: SomeCommand) -> None:
    # Phase 1: załaduj + ustaw status "w trakcie" + commit
    async with self._unit_of_work as unit_of_work:
        workflow = await unit_of_work.workflows.get_by_id(command.workflow_id)
        workflow.mark_running()
        unit_of_work.stage_events(workflow.pull_events())
    # transakcja zapisana, sesja zwolniona

    # Długotrwała operacja zewnętrzna — bez otwartej transakcji
    result = await self._runner.run(...)

    # Phase 2: załaduj ponownie (wersja mogła się zmienić) + zapisz wynik
    async with self._unit_of_work as unit_of_work:
        workflow = await unit_of_work.workflows.get_by_id(command.workflow_id)
        workflow.record_result(result)
        unit_of_work.stage_events(workflow.pull_events())
```

Dlaczego ponowne załadowanie w Phase 2: między fazami inny worker mógł zmienić wersję agregatu. Praca na nieświeżej wersji prowadzi do `WorkflowConcurrentlyModified` lub cichej utraty zmian konkurencyjnych.

## Handler — bezstanowy

Handler nigdy nie przechowuje mutowalnego stanu między wywołaniami `handle()`. Wszystkie dane pochodzą z parametrów komendy/eventu lub z repozytoriów. Jeśli potrzebujesz zachować stan między krokami (np. licznik prób), zapisz go w domenie i odczytaj z repozytorium.

## DTO (Data Transfer Object)

- W `application/dto/` — proste dataclasses lub Pydantic modele
- Służą wyłącznie do przenoszenia danych między warstwami
- Nigdy nie zawierają logiki biznesowej

## Mapper

- W `application/mappers/` — konwersja Entity ↔ DTO
- Statyczne metody lub osobne klasy
- Mapper jest własnością warstwy aplikacyjnej

Każde pole DTO musi mieć źródło. Hardcoded `[]` albo `""` zamiast mapowania to sygnał, że refaktoryzacja agregatu nie została domknięta w warstwie aplikacyjnej — DTO stanie się niezgodne ze stanem domenowym i zwróci klientowi puste/źle dane.

## Strategy — NodeExecutionStrategy

- W `application/strategies/graph_node_execution_strategy/`
- `protocol.py` definiuje kontrakt (Protocol) z adnotacją `@runtime_checkable`
- `_base_strategy.py` — wspólna logika dla wszystkich strategii (budowa Manifest + runner.run)
- Klasy strategii różnią się tylko wartością `mode`: `AgentStrategy`, `RouterStrategy`, `TaskerStrategy`, `ToolStrategy`, `WorkerStrategy`
- Strategie są singletonami w rejestrze — nie dodawaj stanu mutowalnego do strategii
- `registry.py` — rejestr dostępnych strategii z rzucaniem `InvalidNodeMode` dla nieznanych trybów
- Nowy tryb = nowa klasa `*Strategy(mode="nazwa")` + rejestracja w `registry.py`

## Application Port (Protocol)

- W `application/ports/` — interfejsy dla adapterów infrastrukturalnych
- Każdy w osobnym module (`unit_of_work.py`, `time.py`, `logging.py`)
- Obowiązkowe porty: `UnitOfWork`, `Clock`, `IdGenerator`, `EventPublisher`, `Logger`, `GraphNodeExecutionProcessRunner`, `GraphNodeExecutionWorkspace`, `TaskExecutionLoader`
- `ports.py` agreguje re-exporty dla wygody

## `from __future__ import annotations`

Każdy plik `.py` w `domain/`, `application/`, `infrastructure/`, `framework/`, `bootstrap/`, `shared/` zaczyna się od `from __future__ import annotations`. Pozwala to na odroczoną ewaluację typów, używanie typów w stringach w blokach `TYPE_CHECKING`, unikanie circular imports.

Wyjątki (nie wymagają): puste `__init__.py`, pliki migracji Alembic (`versions/*.py`), pliki testowe (`tests/`).

## `TYPE_CHECKING` — zakaz dla class base i isinstance

Typy używane w bazie klasy (`class Foo(Entity[SomeId])`), w `isinstance()`, albo w `@dataclass` z `__post_init__` używającym tego typu — muszą być importowane w runtime (nie pod `TYPE_CHECKING`). `from __future__ import annotations` deferuje tylko adnotacje, nie bazę klasy ani isinstance.

```python
from __future__ import annotations
from shell.domain.value_objects.ids import SomeId   # runtime — używane w class base

if TYPE_CHECKING:
    from shell.domain.other import SomeOther         # tylko adnotacje
```

## Factory / Bus — zakaz `Any` escape

W plikach factory nie używaj `Any` do pomijania type-checkingu. Używaj `providers.Container[T]` lub jawnych typów kontenera zamiast `Any` + `type: ignore`.
