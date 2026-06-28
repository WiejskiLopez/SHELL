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
- Jeśli reakcja na event wymaga koordynacji wielu agregatów — należy użyć Process Managera (sagi), który wysyła osobne komendy.

## Klasa

- Import eventu w sekcji głównej (nie w TYPE_CHECKING) — handler jawnie deklaruje jaki event obsługuje.
- Porty repozytoriów i serwisów w TYPE_CHECKING — zależności infrastrukturalne wstrzykiwane przez DI.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.workflow.events.workflow_started_event import WorkflowStartedEvent

if TYPE_CHECKING:
    from shell.domain.platform.ports import UnitOfWork
    from shell.domain.execution.services.eligibility_port import EligibilityPort
```

## Metoda handle

- Pojedyncza `async handle(self, event: TEvent) -> None`.

## Struktura metody — wzorzec

```python
async def handle(self, workflow_started_event: WorkflowStartedEvent) -> None:
    async with self._unit_of_work as unit_of_work:
        # 1. Idempotentność — sprawdź czy event już przetworzony
        if await unit_of_work.inbox_repository.contains(workflow_started_event.event_id):
            return

        # 2. Budujemy agregat z repozytorium
        workflow = await unit_of_work.workflow_repository.get_by_id(
            workflow_started_event.workflow_id
        )
        if workflow is None:
            # 3. Normalne przy eventual consistency — warning, nie błąd
            self._logger.warning('Workflow %s not found', workflow_started_event.workflow_id)
            return

        # 4. Przez serwisy domenowe (porty w module agregatu)
        #    dostarczamy agregatowi kompletny dataset do decyzji
        eligibility = await self._eligibility_service.check(workflow.owner_id)

        # 5. Wołamy metodę agregatu z kompletem parametrów
        workflow.confirm_started(eligibility=eligibility, now=self._clock.now())

        # 6. W tej samej transakcji: zapis + eventy + inbox
        unit_of_work.workflow_repository.save(workflow)
        unit_of_work.stage_events(workflow.pull_events())
        unit_of_work.inbox_repository.add(workflow_started_event.event_id)
```

## Idempotentność

- Handler **musi** być idempotentny — wielokrotne przetworzenie tego samego eventu daje ten sam efekt.
- **Inbox pattern**: sprawdź czy `event_id` jest już w tabeli inbox. Jeśli tak → `return`. Jeśli nie → przetwórz + oznacz jako przetworzone w **tej samej transakcji**.
- Inbox check to **pierwsza** operacja w metodzie `handle` — fail-fast.

```python
# Obowiązkowy pierwszy krok w każdym event handlerze
if await unit_of_work.inbox_repository.contains(event.event_id):
    return
```

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
- `inbox_repository.add(event_id)` w tej samej transakcji co zmiana domenowa.

## Logowanie

- Log warning gdy agregat nie istnieje — normalne przy eventual consistency.
- Log debug przy pominięciu zdublowanego eventu (inbox hit).

> **Reguły nazewnictwa → [naming-convention-standard](../../naming-standards/naming-convention-standard/SKILL.md#handlers)**

## Lokalizacja

- `shell/application/<bc>/event_handlers/`

## Cross-BC

- Handler aplikacyjny nie może bezpośrednio wołać agregatów, serwisów domenowych, repozytoriów ani żadnych innych elementów należących do innej domeny.
- Zamiast tego używa portu (protokołu) zdefiniowanego w `application/ports/` lub domenie docelowej.
