# Domain Event Handler Structure

> Reguły struktury Domain Event Handler we wszystkich bounded contextach.

## Definicja

- Event Handler to komponent warstwy aplikacyjnej, który subskrybuje konkretny Domain Event i wykonuje reakcję biznesową.

## Klasa

- Import eventu w sekcji głównej (nie w TYPE_CHECKING) — handler jawnie deklaruje jaki event obsługuje.
- Porty w TYPE_CHECKING — zależności infrastrukturalne wstrzykiwane przez DI.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.workflow.events.workflow_started_event import WorkflowStartedEvent

if TYPE_CHECKING:
    from shell.domain.platform.ports import UnitOfWork
    from shell.domain.notification.ports import NotificationPort
```

## Metoda handle

- Pojedyncza `async handle(self, event: TEvent) -> None`.

## Idempotentność

- Handler musi być idempotentny — wielokrotne przetworzenie tego samego eventu daje ten sam efekt.
- Inbox pattern: sprawdź czy `event_id` jest już w tabeli inbox. Jeśli tak → skip. Jeśli nie → przetwórz + oznacz jako przetworzone w tej samej transakcji.

```python
async def handle(self, event: WorkflowStartedEvent) -> None:
    async with self._unit_of_work as unit_of_work:
        if await unit_of_work.inbox.contains(event.event_id):
            return
        workflow = await unit_of_work.workflows.get_by_id(event.workflow_id)
        if workflow is None:
            self._logger.warning('Workflow %s not found', event.workflow_id)
            return
        notification = Notification.from_event(event)
        unit_of_work.notifications.save(notification)
        unit_of_work.stage_events(notification.pull_events())
        unit_of_work.inbox.add(event.event_id)
```

## Logowanie

- Log warning gdy agregat nie istnieje — normalne przy eventual consistency.

## Lokalizacja

- `shell/application/<bc>/event_handlers/`

## Cross-BC

- Handler aplikacyjny nie może bezpośrednio wołać agregatów, serwisów domenowych, repozytoriów ani żadnych innych elementów należących do innej domeny.
- Zamiast tego używa portu (protokołu) zdefiniowanego w `application/ports/` lub domenie docelowej.
