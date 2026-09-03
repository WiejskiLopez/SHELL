---
name: command-handler-structure
description: Reguły struktury Command Handler — koordynacja bez logiki biznesowej, UoW, stage_events, TYPE_CHECKING dla portów.
---

# Command Handler Structure

> Reguły struktury Command Handler (Application Service) we wszystkich bounded contextach.

## Definicja

- Command Handler koordynuje wykonanie komendy; logikę biznesową deleguje do agregatu domenowego.
- Zadaniem handlera jest:
  1. Zbudować agregat domenowy z repozytorium (lub utworzyć nowy przez factory).
  2. Poprzez serwisy domenowe / porty dostarczyć agregatowi kompletny dataset do podjęcia decyzji (porty zdefiniowane w module agregatu).
  3. Wywołać odpowiednią metodę agregatu ze wszystkimi parametrami.
  4. W tej samej transakcji zapisać zmieniony agregat do repozytorium — `unit_of_work.save(repo_type, agregat)` sam wyciąga `pull_events()` i stawia je w outboxie.

## Jedna komenda = jeden agregat

- Command Handler może modyfikować stan **maksymalnie jednego agregatu** domenowego w ramach jednej komendy.
- Handler ładuje **jeden** agregat z repozytorium, woła **jedną** metodę domenową (lub tworzy nowy agregat przez factory), zapisuje **jeden** agregat.
- Każdy handler modyfikuje maksymalnie jeden agregat; koordynację wielu agregatów realizują
  wzorce z `pattern-standards/saga-structure` (Event Chain / Saga), a reakcję na eventy —
  `pattern-standards/event-handler-structure`.

### Przykład antywzorca (multi-aggregate w jednym handlerze)

```python
async def handle(self, command: SomeCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        order = await unit_of_work.repository(OrderRepository).get_by_id(...)
        task = await unit_of_work.repository(TaskRepository).get_by_id(...)

        # Modyfikuje 2 agregaty w jednym handlerze — antywzorzec
        order.complete(...)
        task.start(...)

        await unit_of_work.save(OrderRepository, order)  # 1. agregat
        await unit_of_work.save(TaskRepository, task)    # 2. agregat — antywzorzec
```

## Klasa

- Nazwa klasy command handlera musi miec postac `<Operation><Aggregate>Handler`.
- Nazwa pliku command handlera musi miec postac `<operation>_<aggregate>_handler.py`.
- Nazwa operacji musi zawierac agregat, którego stan zmienia handler.
- Zależności wstrzykiwane przez konstruktor.
- Porty repozytoriów i serwisów w TYPE_CHECKING.
- Import komendy może być w TYPE_CHECKING — używana tylko w sygnaturze `handle()`.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.my_service.application.my_bc.my_aggregate.commands.start_workflow_command import (
        StartWorkflowCommand,
    )
    from shell.my_service.domain.my_bc.aggregates.my_aggregate.repositories.my_aggregate_repository import (
        MyAggregateRepository,
    )
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
```

## Metoda handle

- Pojedyncza `async handle(self, command: <CommandName>) -> <ResultDto> | None`.
- Komenda modyfikuje stan agregatu; wynik operacji handler zwraca jako **DTO** (frozen dataclass),
  a nie surowy `str` czy agregat.

## Struktura metody — wzorzec (API UnitOfWork SHELL)

```python
async def handle(self, command: CompleteOrderCommand) -> CompleteOrderResult:
    async with self._unit_of_work as unit_of_work:
        # 1. Budujemy agregat z repozytorium (port jako klasa — repository())
        order = await unit_of_work.repository(OrderRepository).get_by_id(
            OrderId(command.order_id)
        )

        # 2. Przez porty dostarczamy agregatowi kompletny dataset do decyzji
        pricing = await self._pricing_service.calculate(order.items)
        eligibility = await self._eligibility_service.check(order.customer_id)

        # 3. Wołamy metodę agregatu z kompletem parametrów
        order.complete(pricing=pricing, eligibility=eligibility, now=self._clock.now())

        # 4. Zapis — save() wyciąga pull_events() i stage'uje je do outboxa
        await unit_of_work.save(OrderRepository, order)

    return CompleteOrderResult(order_id=order.id.value)
```

## Porty — korzystanie z portów w handlerze

- Wszystko czego agregat wymaga do podjęcia decyzji (kalkulacje, walidacje krzyżowe, dane z innych agregatów/subdomen/mikroserwisów) jest dostarczane przez **porty zewnętrzne** (Provider dla odczytu, Command Port dla operacji).
- Handler wstrzykuje implementacje tych portów, wywołuje je przed metodą agregatu i przekazuje wyniki (Value Objecty) jako parametry.
- Agregat korzysta z danych przekazanych przez parametry wywołania, a porty infrastrukturalne pozostaja w warstwie aplikacji.
- Definicje portów i adapterów opisują wzorce Aggregate Provider (odczyt) i Command Port (operacje).

## Zero decyzji w handlerze

- Handler koordynuje wykonanie; decyzje biznesowe podejmuje agregat:
  - Stan agregatu ewaluuje metoda domenowa (guard/invariants); handler przekazuje komplet parametrów z portów
  - Handler wywołuje jedną metodę domenową właściwą dla danej komendy
  - Zapis wykonuje `unit_of_work.save(...)` automatycznie na zakończenie
- Zakres działań handlera:
  - **Błąd infrastrukturalny** — np. błąd bazy danych, timeout sieciowy (propagowany z repozytorium/serwisu)
  - **Błąd domenowy** — rzucony przez agregat/serwis domenowy przy naruszeniu invariantu (np. `OrderAlreadyCompleted`, `WorkflowNotRunning`)
- **Obsługa błędów**: handler propaguje błędy domenowe wyżej (do warstwy framework/API).

## Koordynacja, delegacja do agregatu

```python
# Poprawnie — delegacja do agregatu
order.complete(pricing=pricing, eligibility=eligibility, now=now)

# Antywzorzec — logika biznesowa w handlerze
if order.status == OrderStatus.PENDING:
    order.status = OrderStatus.COMPLETED
    ...
```

## UoW

- `async with self._unit_of_work as unit_of_work:` — UoW jako async context manager.
- Port `UnitOfWork` (`shell/platform/application/ports/persistence/unit_of_work.py`) oferuje:
  - `repository(repo_type: type) -> Any` — pobranie repozytorium przez klasę portu;
  - `await save(repo_type: type, aggregate: object)` — zapis agregatu, automatycznie `pull_events()` → `stage_events` (outbox);
  - `stage_events(events)` — wołany automatycznie przez `save()`; ręczne wołanie przy `save()` tworzy double-staging.
- `commit()` wykonuje `__aexit__` UoW przy braku wyjątku; `rollback()` przy wyjątku.
- Handler przekazuje zapis i commit do UoW; bezpośrednie `unit_of_work.commit()` w handlerze nie występuje.
- `stage_events(...)` używasz bezpośrednio wyłącznie wtedy, gdy agregat zapisujesz spoza `save()` (przypadek nietypowy).

## Walidacja

- **Strukturalna** (typy, formaty, zakresy) — na granicy API, przez Pydantic w warstwie framework.
- **Komendy** — walidacja w `__post_init__` (dataclass).
- **Biznesowa** — w domenie (Value Object w `__post_init__`, guard clauses w agregacie).
- Handler przekazuje dane; walidację biznesową wykonuje domena.

## Obsługa błędów

- **Błędy domenowe** (`DomainError`) — propagują do frameworka; retry/logowanie może przejąć middleware.
- **Błędy infrastrukturalne** (`RepositoryException`) — propagują wyżej.
- `ConcurrentModificationError` (optymistyczne blokowanie) — przechwytywany wyłącznie dla retry/logowania.
- Handler przekazuje błędy logiki biznesowej z warstwy domenowej dalej.

## Lokalizacja

- `shell/<service>/application/<bc>/<aggregate>/command_handlers/`

## Bezpieczeństwo

- Handler importuje wyłącznie z warstwy application/domain.