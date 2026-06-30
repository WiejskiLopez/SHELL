---
name: event-handler-structure
description: Reguły struktury Event Handler — subskrypcja eventów, idempotencja przez inbox, rejestracja w EventBus.
---

# Domain Event Handler Structure

> Reguły struktury Domain Event Handler we wszystkich bounded contextach.

## Definicja

- Event Handler to komponent warstwy aplikacyjnej, który subskrybuje konkretny Domain Event i wykonuje reakcję biznesową.
- Analogicznie do Command Handlera: buduje agregat z repozytorium, dostarcza mu dane przez serwisy (porty w module agregatu), wywołuje metodę agregatu, zapisuje + publikuje eventy.
- **Różnica vs Command Handler**: event handler musi być idempotentny (inbox pattern) i tolerować brak agregatu (eventual consistency).

## Jedna reakcja = jeden agregat

- Event Handler może modyfikować stan **maksymalnie jednego agregatu** domenowego w ramach jednej reakcji.
- Jeśli reakcja na event wymaga koordynacji wielu agregatów — **nigdy nie modyfikuj dwóch agregatów w jednym handlerze**. Stosuj jeden z dwóch wzorców (szczegóły w [handler-structure](../handler-structure/SKILL.md#koordynacja-wielu-agregatów--gdy-1-handler-to-za-mało)):

### Event Chain (choreografia)

Handler A reaguje na event, modyfikuje agregat A → emituje event → Handler B reaguje, modyfikuje agregat B → opcjonalnie event zwrotny do A.

```python
# DOBRY — Event Chain: dwa osobne event handlery, każdy modyfikuje 1 agregat

class WorkflowStartedHandler:
    """Reaguje na WorkflowStartedEvent, modyfikuje tylko TaskExecution."""
    async def handle(self, event: WorkflowStartedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            task = await unit_of_work.repository(TaskExecutionRepository).get_by_id(...)
            if task is None:
                return
            task.execute_in_workflow(event.workflow_id)
            unit_of_work.repository(TaskExecutionRepository).save(task)
            unit_of_work.stage_events(task.pull_events())
            # → TaskExecutionUpdatedEvent → ewentualny next handler
```

### Saga / Process Manager (orkiestracja)

Gdy agregat A emituje event wymagający koordynacji wielu agregatów:
1. Event trafia do Sagi (Process Manager)
2. Saga emituje osobne komendy — **każda modyfikuje dokładnie 1 agregat**
3. Każdy agregat odpowiada eventem do sagi
4. Saga po zebraniu odpowiedzi emituje event końcowy do agregatu A

```python
# DOBRY — Saga: osobne komendy, każda modyfikuje 1 agregat

class NodeExecutionSaga:
    async def handle(self, event: GraphNodeExecutionStartedEvent) -> None:
        await self._command_bus.publish(ExecuteNodeCommand(event.node_id))
        # → ExecuteNodeHandler modyfikuje tylko GraphNodeExecution

    async def handle(self, event: GraphNodeExecutionCompletedEvent) -> None:
        if self._needs_retry(event):
            await self._command_bus.publish(RetryNodeCommand(event.node_id))
        else:
            await self._command_bus.publish(AdvanceWorkflowCommand(event.workflow_id))
            # → AdvanceWorkflowHandler modyfikuje tylko Workflow
```

## Klasa

- Import eventu może być w TYPE_CHECKING — typ używany tylko w sygnaturze `handle()`.
- Porty repozytoriów i serwisów w TYPE_CHECKING — zależności infrastrukturalne wstrzykiwane przez DI.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.workflow.events.workflow_started_event import WorkflowStartedEvent
    from shell.domain.platform.ports import UnitOfWork
    from shell.domain.execution.services.eligibility_port import EligibilityPort
```

## Metoda handle

- Pojedyncza `async handle(self, event: TEvent) -> None`.

## Struktura metody — wzorzec

```python
async def handle(self, workflow_started_event: WorkflowStartedEvent) -> None:
    async with self._unit_of_work as unit_of_work:
        # 1. Budujemy agregat z repozytorium
        workflow = await unit_of_work.workflow_repository.get_by_id(
            workflow_started_event.workflow_id
        )
        if workflow is None:
            # 2. Normalne przy eventual consistency — warning, nie błąd
            self._logger.warning('Workflow %s not found', workflow_started_event.workflow_id)
            return

        # 3. Przez serwisy domenowe (porty w module agregatu)
        #    dostarczamy agregatowi kompletny dataset do decyzji
        eligibility = await self._eligibility_service.check(workflow.owner_id)

        # 4. Wołamy metodę agregatu z kompletem parametrów
        workflow.confirm_started(eligibility=eligibility, now=self._clock.now())

        # 5. W tej samej transakcji: zapis + eventy
        unit_of_work.workflow_repository.save(workflow)
        unit_of_work.stage_events(workflow.pull_events())
```

## Idempotentność

- Handler **musi** być idempotentny — wielokrotne przetworzenie tego samego eventu daje ten sam efekt.
- **Idempotentność jest zapewniana przez InboxProcessor (infrastruktura)** — sprawdza `inbox_event` przed dispatchem do handlera. Event handler sam nie sprawdza inboxa.
- Handler odpowiada za **projektową idempotentność** — guard clauses na stan agregatu przed mutacją (np. `if workflow.status is not WorkflowStatus.IDLE: return`).
- Więcej: [idempotent-handler-pattern](../idempotent-handler-pattern/SKILL.md)

## Zero decyzji biznesowych

- Handler **nie podejmuje żadnych decyzji biznesowych**:
  - Nie sprawdza stanu agregatu przed wywołaniem metody
  - Nie wybiera między ścieżkami reakcji w zależności od parametrów
  - Nie decyduje czy zapisać agregat czy nie
- Handler jedyne co może zrobić to:
  - **Błąd infrastrukturalny** — propagowany z repozytorium/serwisu
  - **Błąd domenowy** — rzucony przez agregat przy naruszeniu invariantu

```python
# DOBRY — delegacja do agregatu
workflow.confirm_started(eligibility=eligibility, now=now)

# ŹLE — logika biznesowa w handlerze
if workflow.status == WorkflowStatus.RUNNING:
    return  # decyzja biznesowa w handlerze!
```

## Porty serwisów w module agregatu

- Wszystko czego agregat wymaga do podjęcia decyzji jest dostarczane przez serwisy domenowe (porty w `domain/<bc>/services/`).
- Handler wstrzykuje implementacje portów, wywołuje je przed metodą agregatu i przekazuje wyniki jako parametry.
- Agregat **nie ma bezpośrednich zależności do portów infrastrukturalnych**.

```python
# Port zdefiniowany w domain/execution/services/eligibility_port.py
class EligibilityPort(Protocol):
    async def check(self, customer_id: CustomerId) -> Eligibility: ...
```

> **Szczegóły implementacji adapterów → [port-adapter-structure](../port-adapter-structure/SKILL.md#adaptery-cross-aggregate-data-retrieval)**

## Agregat nie istnieje

- Przy eventual consistency agregat może nie istnieć w momencie przetworzenia eventu.
- **Nie rzucaj błędu** — zaloguj warning i `return`.
- To normalne, że event dotarł szybciej niż stan agregatu został zapisany.

```python
# DOBRY
if workflow is None:
    self._logger.warning('Workflow %s not found — eventual consistency delay', event.workflow_id)
    return
```

## UoW

- `async with self._unit_of_work as unit_of_work:` — UoW jako async context manager.
- `commit()` na `__aexit__` jeśli brak wyjątku; `rollback()` jeśli wyjątek.
- `stage_events(aggregate.pull_events())` po każdej mutacji agregatu.

## Logowanie

- Log warning gdy agregat nie istnieje — normalne przy eventual consistency.
- Duplicate event detection logowany przez InboxProcessor (infrastruktura), nie w handlerze.

> **Reguły nazewnictwa → [naming-convention-standard](../../naming-standards/naming-convention-standard/SKILL.md#handlers)**

## Lokalizacja

- `shell/application/<bc>/event_handlers/`

## Cross-BC

- Handler aplikacyjny nie może bezpośrednio wołać agregatów, serwisów domenowych, repozytoriów ani żadnych innych elementów należących do innej domeny.
- Zamiast tego używa portu (protokołu) zdefiniowanego w `application/ports/` lub domenie docelowej.
