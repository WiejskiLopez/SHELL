---
name: idempotent-handler-pattern
description: Reguły idempotentności handlerów — inbox pattern, sprawdzanie stanu przed mutacją, deduplikacja eventów.
---

# Idempotent Handler Pattern

> Reguły idempotentności handlerów eventów i komend we wszystkich bounded contextach.

## Definicja

- Każdy handler eventu/komendy musi być idempotentny — wielokrotne wywołanie z tym samym inputem daje ten sam efekt.
- Wymagane przez at-least-once delivery gwarancję outboxa.

## Inbox pattern — warstwa infrastruktury

- Idempotentność jest zapewniana przez **InboxProcessor** na poziomie infrastruktury.
- `InboxProcessor` odczytuje `inbox_event`, sprawdza duplikaty i dispatchuje do handlera tylko dla nieprzetworzonych eventów.
- Event handler **nie sprawdza inboxa** — to odpowiedzialność infrastruktury.

```
[Outbox] → OutboxToInboxRelay → [InboxEvent] → InboxProcessor (dedup) → EventBus → Handler
```

## Guard clauses w handlerze

- Handler odpowiada za **projektową idempotentność** — sprawdzenie stanu agregatu przed mutacją.
- Jeśli agregat już jest w stanie docelowym (event już obsłużony), handler loguje warning i `return`.

```python
async def handle(self, workflow_started_event: WorkflowStartedEvent) -> None:
    async with self._unit_of_work as unit_of_work:
        workflow = await unit_of_work.workflow_repository.get_by_id(workflow_started_event.workflow_id)
        if workflow is None:
            self._logger.warning('Workflow %s not found', workflow_started_event.workflow_id)
            return
        # Guard clause: sprawdź czy event nie został już obsłużony
        if workflow.status is not WorkflowStatus.IDLE:
            self._logger.warning('Workflow %s already started', workflow_started_event.workflow_id)
            return
        workflow.start()
        unit_of_work.stage_events(workflow.pull_events())
```

## Kluczowe zasady

- Idempotentność na poziomie infrastruktury (InboxProcessor) + guard clauses w handlerze.
- Guard clause przed mutacją, nie po.
- Log warning gdy agregat nie istnieje (normalne przy eventual consistency) lub gdy stan wskazuje na już obsłużony event.
- Idempotency key dla API zewnętrznych.
