# Idempotent Handler Pattern

> Reguły idempotentności handlerów eventów i komend we wszystkich bounded contextach.

## Definicja

- Każdy handler eventu/komendy musi być idempotentny — wielokrotne wywołanie z tym samym inputem daje ten sam efekt.
- Wymagane przez at-least-once delivery gwarancję outboxa.

## Inbox pattern

- Inbox przechowuje ID przetworzonych eventów — zapobiega wielokrotnemu przetworzeniu.
- Zapis do inbox jest w TEJ SAMEJ TRANSAKCJI co zmiana domenowa wywołana przez event.

```python
async def handle(self, event: WorkflowStartedEvent) -> None:
    async with self._unit_of_work as unit_of_work:
        # 1. Sprawdź czy już przetworzono
        if await unit_of_work.inbox.contains(event.event_id):
            self._logger.debug('Event %s already processed, skipping', event.event_id)
            return

        # 2. Wykonaj operację
        workflow = await unit_of_work.workflows.get_by_id(event.workflow_id)
        if workflow is None:
            self._logger.warning('Workflow %s not found', event.workflow_id)
            return
        workflow.notify_started(event.started_by)
        unit_of_work.stage_events(workflow.pull_events())

        # 3. Oznacz jako przetworzone (ta sama transakcja)
        unit_of_work.inbox.add(event.event_id)
```

## Sprawdzanie stanu

- Przed mutacją sprawdź czy stan agregatu nie wskazuje że event został już obsłużony.
- W połączeniu z Inbox daje双重 zabezpieczenie.

```python
async def handle(self, event: WorkflowStartedEvent) -> None:
    async with self._unit_of_work as unit_of_work:
        if await unit_of_work.inbox.contains(event.event_id):
            return
        workflow = await unit_of_work.workflows.get_by_id(event.workflow_id)
        if workflow is None:
            return
        if workflow.status is not WorkflowStatus.IDLE:
            self._logger.warning('Workflow %s already started', event.workflow_id)
            return
        workflow.start()
        unit_of_work.stage_events(workflow.pull_events())
        unit_of_work.inbox.add(event.event_id)
```

## Kluczowe zasady

- Inbox + agregat w tej samej transakcji.
- Sprawdzenie przed mutacją, nie po.
- Log warning gdy agregat nie istnieje (normalne przy eventual consistency).
- Idempotency key dla API zewnętrznych.
