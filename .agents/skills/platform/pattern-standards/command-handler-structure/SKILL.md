---
name: command-handler-structure
description: Reguły struktury Command Handler — koordynacja bez logiki biznesowej, UoW, stage_events, TYPE_CHECKING dla portów.
---

# Command Handler Structure

> Reguły struktury Command Handler (Application Service) we wszystkich bounded contextach.

## Definicja

- Command Handler koordynuje wykonanie komendy — **nie zawiera logiki biznesowej**.
- Zadaniem handlera jest:
  1. Zbudować agregat domenowy z repozytorium (lub utworzyć nowy przez factory).
  2. Poprzez serwisy domenowe dostarczyć agregatowi kompletny dataset do podjęcia decyzji (porty serwisów zdefiniowane w module agregatu).
  3. Wywołać odpowiednią metodę agregatu ze wszystkimi parametrami.
  4. W tej samej transakcji zapisać zmieniony agregat do repozytorium oraz opublikować zdarzenia z tą zmianą związane (`stage_events`).

## Jedna komenda = jeden agregat

- Command Handler może modyfikować stan **maksymalnie jednego agregatu** domenowego w ramach jednej komendy.
- Handler ładuje **jeden** agregat z repozytorium, woła **jedną** metodę domenową (lub tworzy nowy agregat przez factory), zapisuje **jeden** agregat.
- Jeśli logika wymaga koordynacji wielu agregatów — **nigdy nie modyfikuj dwóch agregatów w jednym handlerze**. Stosuj jeden z dwóch wzorców:

### Event Chain (choreografia)

Handler A modyfikuje agregat A → emituje event → Handler B (osobny, w tym samym lub innym BC) reaguje i modyfikuje agregat B → opcjonalnie event zwrotny do A.

Stosuj dla prostych sekwencji 2-3 agregatów, gdzie eventual consistency jest akceptowalna.

```python
# DOBRY — Event Chain: dwa osobne handlery, każdy modyfikuje 1 agregat

class WorkflowStartHandler:
    async def handle(self, command: StartWorkflowCommand) -> None:
        async with self._unit_of_work as unit_of_work:
            workflow = Workflow.new(...)
            workflow.start(now=now)
            unit_of_work.repository(WorkflowRepository).save(workflow)
            unit_of_work.stage_events(workflow.pull_events())
        # → WorkflowStartedEvent → TaskExecution reaguje w osobnym handlerze

class WorkflowStartedHandler:
    async def handle(self, event: WorkflowStartedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            task = await unit_of_work.repository(TaskExecutionRepository).get_by_id(...)
            if task is None:
                raise TaskExecutionNotFound(...)
            task.execute_in_workflow(event.workflow_id)
            unit_of_work.repository(TaskExecutionRepository).save(task)
            unit_of_work.stage_events(task.pull_events())
```

### Saga / Process Manager (orkiestracja)

Gdy agregat A musi skoordynować kilka agregatów podrzędnych:
1. Agregat A emituje event → Saga przechwytuje
2. Saga emituje osobne komendy — **każda modyfikuje dokładnie 1 agregat**
3. Każdy agregat odpowiada eventem do sagi
4. Saga po zebraniu odpowiedzi emituje event końcowy do agregatu A

Stosuj gdy potrzeba kompensacji, timeoutów, śledzenia stanu, lub proces ma 3+ agregatów.

```python
# DOBRY — Saga: osobne komendy, każda modyfikuje 1 agregat

class GraphExecutionSaga:
    async def handle(self, event: GraphExecutionStartedEvent) -> None:
        await self._command_bus.publish(ExecuteNodeCommand(...))
        # → ExecuteNodeHandler modyfikuje tylko GraphNodeExecution

    async def handle(self, event: GraphNodeExecutionCompletedEvent) -> None:
        if self._has_more_nodes(event):
            await self._command_bus.publish(ExecuteNodeCommand(next_node))
        else:
            await self._command_bus.publish(AdvanceWorkflowCommand(...))
            # → AdvanceWorkflowHandler modyfikuje tylko Workflow
```

### Przykład ZŁY (zabroniony)

```python
async def handle(self, command: SomeCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        order = await unit_of_work.order_repository.get_by_id(...)
        task = await unit_of_work.task_repository.get_by_id(...)

        # Zapisuje 2 agregaty w jednym handlerze — ZABRONIONE
        order.complete(...)
        task.start(...)

        unit_of_work.order_repository.save(order)        # 1. agregat
        unit_of_work.task_repository.save(task)          # 2. agregat — ŹLE!
        unit_of_work.stage_events(order.pull_events())
        unit_of_work.stage_events(task.pull_events())
```

## Klasa

- Zależności wstrzykiwane przez konstruktor.
- Porty repozytoriów i serwisów w TYPE_CHECKING.
- Import komendy może być w TYPE_CHECKING — używana tylko w sygnaturze `handle()`.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.workflow.commands import StartWorkflowCommand
    from shell.domain.workflow.repository import WorkflowRepository
    from shell.domain.platform.ports import UnitOfWork
```

## Metoda handle

- Pojedyncza `async handle(self, command: TCommand) -> str`.
- Komenda zmienia stan, zwraca ID utworzonego agregatu jako `str`.

## Struktura metody — wzorzec

```python
async def handle(self, command: CompleteOrderCommand) -> str:
    async with self._unit_of_work as unit_of_work:
        # 1. Budujemy agregat z repozytorium
        order = await unit_of_work.order_repository.get_by_id(
            OrderId(command.order_id)
        )

        # 2. Przez serwisy domenowe (porty w module agregatu)
        #    dostarczamy agregatowi kompletny dataset do decyzji
        pricing = await self._pricing_service.calculate(order.items)
        eligibility = await self._eligibility_service.check(order.customer_id)

        # 3. Wołamy metodę agregatu z kompletem parametrów
        order.complete(
            pricing=pricing,
            eligibility=eligibility,
            now=self._clock.now(),
        )

        # 4. W tej samej transakcji: zapis + eventy
        unit_of_work.order_repository.save(order)
        unit_of_work.stage_events(order.pull_events())
```

## Porty serwisów — definicja i implementacja

- Wszystko czego agregat wymaga do podjęcia decyzji (kalkulacje, walidacje krzyżowe, dane z innych agregatów/subdomen/mikroserwisów) jest dostarczane przez **serwisy domenowe**.
- Porty (Protocol) tych serwisów są definiowane w `shell/domain/<bc>/services/` — po stronie **konsumującego** agregatu.
- Handler wstrzykuje implementacje tych portów, wywołuje je przed metodą agregatu i przekazuje wyniki (Value Objecty) jako parametry.
- Agregat **nie ma bezpośrednich zależności do portów infrastrukturalnych** — dostaje wszystkie dane jako parametry wywołania.

```python
# Port zdefiniowany w domain/execution/services/workflow_data_port.py
# (konsumujący definiuje kontrakt)
class WorkflowDataPort(Protocol):
    async def get_workflow_summary(self, workflow_id: WorkflowId) -> WorkflowSummary: ...

class EligibilityPort(Protocol):
    async def check(self, customer_id: CustomerId) -> Eligibility: ...
```

### Implementacja adaptera

Adaptery implementujące te porty znajdują się w `shell/infrastructure/<bc>/services/<nazwa_agregatu>/` — jeden folder grupuje wszystkie adaptery dla danego agregatu.

Jeśli agregat zostanie wydzielony do osobnego mikroserwisu, zmienia się **tylko** zawartość tego folderu (z lokalnego repozytorium na HTTP). Port w domenie i handler w aplikacji pozostają bez zmian.

```python
# shell/infrastructure/execution/services/workflow/
class SqlWorkflowDataAdapter:
    async def get_workflow_summary(self, workflow_id: WorkflowId) -> WorkflowSummary:
        model = await self._repo.get_by_id(workflow_id)
        return self._mapper.to_summary(model)
```



## Zero decyzji w handlerze

- Handler **nie podejmuje żadnych decyzji biznesowych**:
  - Nie sprawdza stanu agregatu przed wywołaniem metody (`if order.status == 'pending': ...`)
  - Nie wybiera między metodami agregatu w zależności od parametrów
  - Nie decyduje czy zapisać agregat czy nie
- Handler jedyne co może zrobić to:
  - **Błąd infrastrukturalny** — np. błąd bazy danych, timeout sieciowy (propagowany z repozytorium/serwisu)
  - **Błąd domenowy** — rzucony przez agregat/serwis domenowy przy naruszeniu invariantu (np. `OrderAlreadyCompleted`, `WorkflowNotRunning`)
- **Obsługa błędów**: handler nie łapie błędów domenowych — propaguje je wyżej (do warstwy framework/API).

## Koordynacja, nie logika

```python
# DOBRY — delegacja do agregatu
order.complete(pricing=pricing, eligibility=eligibility, now=now)

# ŹLE — logika biznesowa w handlerze
if order.status == OrderStatus.PENDING:
    order.status = OrderStatus.COMPLETED
    ...
```

## Przykład ZŁY (zabroniony)

```python
async def handle(self, command: SomeCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        order = await unit_of_work.order_repository.get_by_id(OrderId(command.order_id))
        task = await unit_of_work.task_repository.get_by_id(TaskId(command.task_id))

        # Zapisuje 2 agregaty w jednym handlerze
        order.complete(...)
        task.start(...)

        unit_of_work.order_repository.save(order)
        unit_of_work.task_repository.save(task)
        unit_of_work.stage_events(order.pull_events())
        unit_of_work.stage_events(task.pull_events())
```

## UoW

- `async with self._unit_of_work as unit_of_work:` — UoW jako async context manager.
- `commit()` na `__aexit__` jeśli brak wyjątku; `rollback()` jeśli wyjątek.
- Nigdy ręcznego `unit_of_work.commit()` w handlerze.
- `stage_events(aggregate.pull_events())` po każdej mutacji agregatu.

## Walidacja

- **Strukturalna** (typy, formaty, zakresy) — na granicy API, przez Pydantic w warstwie framework.
- **Komendy** — walidacja w `__post_init__` (dataclass), nie w metodzie `validate()` wołanej przez handler.
- **Biznesowa** — w domenie (Value Object w `__post_init__`, guard clauses w agregacie).
- Handler nie waliduje — deleguje do domeny.

## Obsługa błędów

- **Błędy domenowe** (`DomainError`) — propagują do frameworka, handler nie łapie.
- **Błędy infrastrukturalne** (`RepositoryException`) — propagują, handler nie łapie.
- **Jedyny wyjątek**: `ConcurrentModificationError` (optymistyczne blokowanie) — może być złapany dla retry/logowania.
- Handler nie ma bloków `try/except` na logikę biznesową.

## Lokalizacja

- `shell/application/<bc>/command_handlers/`



## Bezpieczeństwo

- Handler nie importuje infrastruktury.
