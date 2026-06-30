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

    async def handle(self, start_workflow_command: StartWorkflowCommand) -> None:
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

> **Reguły nazewnictwa handlerów → [naming-convention-standard](../../naming-standards/naming-convention-standard/SKILL.md#handlers)**

## Command i Event Handler — wspólne reguły

Command Handlery i Event Handlery stosują analogiczne reguły struktury:

| Zasada | Command Handler | Event Handler |
|--------|:---:|:---:|
| Modyfikuje max 1 agregat | ✅ | ✅ |
| Zero decyzji biznesowych | ✅ | ✅ |
| Porty serwisów w module agregatu | ✅ | ✅ |
| save + stage_events | ✅ | ✅ |
| Idempotentność (guard clauses) | ❌ | ✅ |
| Tolerancja braku agregatu | ❌ (błąd) | ✅ (warning) |

> Szczegółowe reguły: [command-handler-structure](../command-handler-structure/SKILL.md) · [event-handler-structure](../event-handler-structure/SKILL.md)

## Koordynacja wielu agregatów — gdy 1 handler to za mało

Gdy logika wymaga modyfikacji więcej niż jednego agregatu, **nigdy nie robimy tego w jednym handlerze/transakcji**. Zamiast tego stosujemy jeden z dwóch wzorców.

### Opcja 1: Event Chain (choreografia)

Handler A modyfikuje agregat A → emituje event → Handler B reaguje, modyfikuje agregat B → opcjonalnie event zwrotny do A dla spójności (z guard clause `if already_processed: return` by uniknąć cykli).

```python
# Handler A: modyfikuje tylko Workflow
async def start_workflow(self, command: StartWorkflowCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        workflow = Workflow.new(...)
        workflow.start(now=now)
        unit_of_work.repository(WorkflowRepository).save(workflow)
        unit_of_work.stage_events(workflow.pull_events())
    # → WorkflowStartedEvent, na który reaguje TaskExecution

# Handler B: reaguje na event, modyfikuje tylko TaskExecution
async def handle(self, event: WorkflowStartedEvent) -> None:
    async with self._unit_of_work as unit_of_work:
        task = await unit_of_work.repository(TaskExecutionRepository).get_by_id(...)
        if task is None:
            self._logger.warning(...)
            return
        task.execute_in_workflow(event.workflow_id)
        unit_of_work.repository(TaskExecutionRepository).save(task)
        unit_of_work.stage_events(task.pull_events())
```

**Stosuj gdy:**
- Prosta sekwencja: A → B (maksymalnie 2-3 agregaty)
- Kompensacja nie jest wymagana
- Eventual consistency jest akceptowalna
- Relacja 1:1 między zdarzeniami — jeden event wywołuje jedną reakcję

### Opcja 2: Saga / Process Manager (orkiestracja)

Gdy agregat A musi skoordynować kilka agregatów podrzędnych w ramach jednego procesu:
1. Agregat A emituje event → Saga Process Manager przechwytuje
2. Saga emituje osobne komendy — **każda trafia do osobnego handlera, każda modyfikuje dokładnie 1 agregat**
3. Każdy agregat po mutacji emituje event do sagi
4. Saga po zebraniu wszystkich odpowiedzi emituje event końcowy do agregatu A, który zmienia swój status informując o wykonaniu procesu

```python
class GraphExecutionSaga:
    """Saga koordynująca proces wykonania grafu — każda komenda modyfikuje 1 agregat."""

    async def handle(self, event: GraphExecutionStartedEvent) -> None:
        # Krok 1: saga emituje komendę — osobny handler modyfikuje 1 agregat
        await self._command_bus.publish(ExecuteNodeCommand(...))
        # → ExecuteNodeHandler modyfikuje tylko GraphNodeExecution
        # → emituje GraphNodeExecutionCompletedEvent

    async def handle(self, event: GraphNodeExecutionCompletedEvent) -> None:
        # Krok 2: saga odbiera wynik, decyduje o kolejnym kroku
        if self._has_next_node(event):
            await self._command_bus.publish(ExecuteNodeCommand(next_node))
        else:
            await self._command_bus.publish(AdvanceWorkflowCommand(...))
            # → AdvanceWorkflowHandler modyfikuje tylko Workflow
            # → emituje WorkflowCompletedEvent → agregat A reaguje

    async def handle(self, event: WorkflowCompletedEvent) -> None:
        # Krok 3: proces zakończony — saga notuje zamknięcie
        await self._saga_repository.mark_completed(event.correlation_id)
```

**Stosuj gdy:**
- Proces ma wiele kroków (3+ agregaty)
- Potrzebne śledzenie stanu, timeouty, retry
- Potrzebna kompensacja (rollback przy błędzie)
- Ten sam agregat pojawia się w kilku krokach procesu
- Komunikacja między Bounded Contextami

### Tabela decyzyjna: Event Chain vs Saga

| Kryterium | Event Chain | Saga |
|-----------|:---:|:---:|
| Liczba agregatów | 2-3 | 3+ |
| Potrzebna kompensacja / rollback | ❌ | ✅ |
| Śledzenie stanu procesu | ❌ | ✅ |
| Timeout / retry | ❌ | ✅ |
| Ten sam agregat w kilku krokach | ❌ | ✅ |
| Cross-BC | ❌ | ✅ |
| Eventual consistency | ✅ | ✅ |
| Prostota implementacji | ✅ | ⚠️ (więcej kodu) |

**Zasada ogólna:** jeśli masz wątpliwości — zacznij od Event Chain. Jeśli pojawi się potrzeba kompensacji, timeoutu lub ten sam agregat występuje w kilku krokach — refaktoruj do Sagi.

## Obsługa błędów

Wszystkie handlery stosują następujące reguły obsługi błędów:

1. **Błędy domenowe propagują** — jeśli agregat lub serwis domenowy rzuci `DomainError`, handler nie łapie go. Błąd propaguje do warstwy framework/API.
2. **Błędy infrastrukturalne propagują** — `RepositoryException`, `ConnectionError` itp. nie są łapane w handlerze.
3. **Jeden wyjątek: `ConcurrentModificationError`** (optymistyczne blokowanie) — może być złapany w handlerze dla retry lub logowania, jeśli jest to zamierzone.
4. **Brak `try/except` na logikę biznesową** — handler nie ma bloków `try/except` które łapią błędy domenowe. Jedyny dozwolony przypadek: async execution gdzie błąd wykonania jest normalnym scenariuszem (np. `GraphNodeExecutionWorker`).

## Logowanie

1. **Event handler** — `logger.warning()` gdy agregat nie istnieje (normalne przy eventual consistency).
2. **Command handler** — nie loguje na poziomie handlera. Logowanie jest realizowane przez middleware (np. `LoggingMiddleware`).
3. **Query handler** — nie loguje. Logowanie zapytań jest poza handlerem.
4. **Audit log** — realizowany przez dedykowany `EventBus` subscriber (np. `LogAuditHandler`), nie przez handler biznesowy.

## Lokalizacja

- Command handlers: `shell/application/<bc>/command_handlers/`
- Query handlers: `shell/application/<bc>/query_handlers/`
- Event handlers: `shell/application/<bc>/event_handlers/`
