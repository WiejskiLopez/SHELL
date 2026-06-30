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

## Idempotentność na poziomie domeny

- Agregat sam odpowiada za swoją idempotentność — metody domenowe sprawdzają wewnętrznie czy operacja jest dozwolona w danym stanie.
- Jeśli agregat jest już w stanie docelowym (event już obsłużony), metoda domenowa jest **idempotentna** (nie zmienia stanu, nie rzuca błędu) lub rzuca `DomainError` jeśli to invariant.
- Handler nie podejmuje decyzji biznesowych — deleguje do agregatu.

```python
async def handle(self, event: WorkflowStartedEvent) -> None:
    async with self._unit_of_work as unit_of_work:
        workflow = await unit_of_work.workflow_repository.get_by_id(event.workflow_id)
        if workflow is None:
            raise WorkflowNotFound(event.workflow_id)
        workflow.start(now=self._clock.now())
        unit_of_work.workflow_repository.save(workflow)
        unit_of_work.stage_events(workflow.pull_events())
```

## Kluczowe zasady

- Deduplikacja na poziomie infrastruktury (InboxProcessor) — handler nie sprawdza inboxa.
- Idempotentność na poziomie domeny — agregat sam decyduje czy operacja jest dozwolona.
- Handler nie sprawdza stanu agregatu — deleguje do domeny.
- Brak agregatu to błąd — handler rzuca wyjątkiem, nie loguje warninga i nie ignoruje.
- Optimistic locking (`ConcurrentModificationError`) zabezpiecza przed race conditions na poziomie repozytorium.
- Idempotency key dla API zewnętrznych.
