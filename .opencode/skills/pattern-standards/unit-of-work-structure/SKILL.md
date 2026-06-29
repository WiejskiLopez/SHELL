---
name: unit-of-work-structure
description: Reguły struktury Unit of Work — async context manager, transakcje, outbox, two-phase UoW dla długotrwałych operacji.
---

# Unit of Work Structure

> Reguły struktury Unit of Work we wszystkich bounded contextach.

## Definicja

- Unit of Work zarządza transakcjami i koordynuje zapis eventów do outboxa.

## Klasa

- UnitOfWork jest zawsze async context managerem.

```python
class UnitOfWork(ABC):
    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(self, exc_type: type[BaseException] | None, ...) -> None: ...

    @abstractmethod
    def stage_events(self, events: list[DomainEvent]) -> None: ...
```

## Implementacja

- `commit()` na `__aexit__` jeśli brak wyjątku.
- `rollback()` jeśli wyjątek.
- Outbox zapisywany w tej samej transakcji co zmiany domenowe.

```python
class SqlUnitOfWork:
    def __init__(self, session_factory: Callable[[], AsyncGenerator[AsyncSession, None]]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._events: list[DomainEvent] = []

    async def __aenter__(self) -> Self:
        self._session = await anext(self._session_factory())
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, ...) -> None:
        try:
            if exc_type is None:
                await self._commit()
            else:
                await self._session.rollback()
        finally:
            await self._session.close()

    async def _commit(self) -> None:
        for event in self._events:
            self._session.add(OutboxEvent.from_domain_event(event))
        await self._session.commit()

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._events.extend(events)
```

## Użycie w handlerze

```python
async def handle(self, start_workflow_command: StartWorkflowCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        workflow = Workflow.create(...)
        unit_of_work.workflow_repository.save(workflow)
        unit_of_work.stage_events(workflow.pull_events())
```

## Two-phase UoW

- Gdy długa operacja zewnętrzna występuje między załadowaniem agregatu a zapisaniem wyniku, użyj dwóch osobnych bloków UoW.
- Phase 1: załaduj agregat, ustaw status "in-progress", commituj (zwolnij transakcję).
- Phase 2: po długiej operacji, przeładuj agregat (wersja mogła się zmienić), zapisz wynik, commituj.

```python
async def handle(self, process_workflow_command: ProcessWorkflowCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        workflow = await unit_of_work.workflow_repository.get_by_id(process_workflow_command.workflow_id)
        workflow.mark_processing()
        unit_of_work.stage_events(workflow.pull_events())

    result = await self._external_service.run(workflow.id)

    async with self._unit_of_work as unit_of_work:
        workflow = await unit_of_work.workflow_repository.get_by_id(process_workflow_command.workflow_id)
        workflow.complete(result)
        unit_of_work.stage_events(workflow.pull_events())
```

## Lokalizacja

- `shell/infrastructure/platform/unit_of_work.py`
