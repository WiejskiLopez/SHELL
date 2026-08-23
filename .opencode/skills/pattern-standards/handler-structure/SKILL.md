---
name: handler-structure
description: Reguły struktury handlerów — bezstanowość, UoW jako context manager, stage_events, zakaz logiki biznesowej.
---

# Handler Structure

> Wspólne reguły struktury wszystkich handlerów (command, query, event) we wszystkich bounded contextach.

## Definicja

- Handler to komponent warstwy aplikacyjnej, który odbiera komendę/zapytanie/event i koordynuje wykonanie.

## Jeden handler = jeden typ

- Jeden handler obsługuje dokładnie jeden typ komendy/zapytania/eventu.
- Command/Query bus: mapowanie 1:1 typu na handler.
- Event bus: 1:N (jeden event może mieć wielu subskrybentów), ale każdy subskrybent pozostaje 1:1 z typem eventu.
- **Wyjątek**: Saga handler (Cycle B) może użyć Union type dla powiązanych eventów (np. `Completed | Failed`), gdzie logika jest rozgałęziona na `isinstance`. To akceptowalne tylko dla handlerów w warstwie `process/` lub gdy oba eventy są wzajemnie wykluczającymi się wynikami tego samego procesu.

```python
class WorkflowStartHandler:
    def __init__(self, ...) -> None:
        ...

    async def handle(self, command: StartWorkflowCommand) -> None:
        ...
```

## Metoda handle

- Pojedyncza publiczna metoda `async handle(self, command/query/event) -> None | DTO`.
- Typ przyjmowany: konkretna komenda/zapytanie/event.
- Typ zwracany: `None` dla command/event, DTO/read model dla query.

## Stateless

- Handler nie przechowuje stanu między wywołaniami.
- Wszystkie dane pochodzą z parametrów lub repozytoriów.
- Jedynymi polami instancji są wstrzyknięte zależności (porty).

## DI

- Zależności wstrzykiwane przez konstruktor.
- Porty/Protocol w TYPE_CHECKING.
- Import command/query/event może być w TYPE_CHECKING — typ używany tylko w sygnaturze `handle()`, nie w runtime.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.workflow.commands import StartWorkflowCommand
    from shell.domain.workflow.repository import WorkflowRepository
```



## Command i Event Handler — wspólne reguły

Command Handlery i Event Handlery stosują analogiczne reguły struktury:

| Zasada | Command Handler | Event Handler |
|--------|:---:|:---:|
| Modyfikuje max 1 agregat | ✅ | ✅ |
| Zero decyzji biznesowych | ✅ | ✅ |
| Porty serwisów w module agregatu | ✅ | ✅ |
| save + stage_events | ✅ | ✅ |
| Brak agregatu w repozytorium | ❌ (błąd) | ❌ (błąd) |


## Koordynacja wielu agregatów — gdy 1 handler to za mało

Gdy logika wymaga modyfikacji więcej niż jednego agregatu, nigdy nie robimy tego w jednym handlerze/transakcji. Koordynację wieloagregatową opisuje `pattern-standards/saga-structure`:

- Event Chain (choreografia) — prosta sekwencja A → B.
- Saga / Process Manager (orkiestracja) — proces wieloagregatowy, kompensacja, timeout, cross-BC.

Handler pozostaje ograniczony do **dwóch modeli wykonania**: (1) reakcja 1:1 na jeden typ, (2) wyjątkowo Union type w handlerach warstwy `process/` (patrz Definicja). Zasada kardynalna: jeden handler modyfikuje maksymalnie jeden agregat.

## Obsługa błędów

Wszystkie handlery stosują następujące reguły obsługi błędów:

1. **Błędy domenowe propagują** — jeśli agregat lub serwis domenowy rzuci `DomainError`, handler nie łapie go. Błąd propaguje do warstwy framework/API.
2. **Błędy infrastrukturalne propagują** — `RepositoryException`, `ConnectionError` itp. nie są łapane w handlerze.
3. **Jeden wyjątek: `ConcurrentModificationError`** (optymistyczne blokowanie) — może być złapany w handlerze dla retry lub logowania, jeśli jest to zamierzone.
4. **Brak `try/except` na logikę biznesową** — handler nie ma bloków `try/except` które łapią błędy domenowe. Jedyny dozwolony przypadek: async execution gdzie błąd wykonania jest normalnym scenariuszem (np. `NodeExecutionWorker`).

## Logowanie

1. **Event handler** — nie loguje na poziomie handlera. Brak agregatu skutkuje wyjątkiem propagowanym wyżej.
2. **Command handler** — nie loguje na poziomie handlera. Logowanie jest realizowane przez middleware (np. `LoggingMiddleware`).
3. **Query handler** — nie loguje. Logowanie zapytań jest poza handlerem.
4. **Audit log** — realizowany przez dedykowany subscriber event bus, nie przez handler biznesowy (patrz `application-layer/middleware-pipeline`).

## Lokalizacja

- Command handlers: `shell/application/<bc>/command_handlers/`
- Query handlers: `shell/application/<bc>/query_handlers/`
- Event handlers: `shell/application/<bc>/event_handlers/`
