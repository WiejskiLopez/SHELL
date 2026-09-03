---
name: unit-of-work-structure
description: Reguły struktury Unit of Work — async context manager, transakcje, outbox, two-phase UoW dla długotrwałych operacji.
---

# Unit of Work Structure

> Reguły struktury Unit of Work w warstwie infrastruktury platformy.

## Definicja

- Unit of Work zarządza transakcjami i koordynuje zapis eventów do outboxa.

## Port

- Port `UnitOfWork` (`shell/platform/application/ports/persistence/unit_of_work.py`) to Protocol używany przez handlery:

```python
class UnitOfWork(Protocol):
    def repository(self, repo_type: type[Any]) -> Any ...
    def stage_events(self, events: Sequence[object]) -> None ...
    async def save(self, repo_type: type, aggregate: object) -> None ...
    @property
    def events(self) -> Sequence[object] ...
    async def commit(self) -> None ...
    async def rollback(self) -> None ...
    async def __aenter__(self) -> UnitOfWork ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None ...
```

## Implementacja

- Bazą implementacji SQL jest `SqlAlchemyUnitOfWorkBase` w `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`; każdy BC dostarcza własną podklasę z mapą portów repozytoriów → klas SQL (per BC, z własną sesją DATABASE_URL).
- `commit()` na `__aexit__` jeśli brak wyjątku; `rollback()` jeśli wyjątek.
- Outbox zapisywany w tej samej transakcji co zmiany domenowe.
- `save(repo_type, aggregate)` zapisuje agregat, wyciąga `aggregate.pull_events()` i woła `stage_events` — eventy domowe trafiają do outboxa automatycznie.

## Użycie w handlerze

```python
async def handle(self, command: StartWorkflowCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        workflow = Workflow.create(...)
        await unit_of_work.save(WorkflowRepository, workflow)
```

## Two-phase UoW

- Gdy długa operacja zewnętrzna występuje między załadowaniem agregatu a zapisaniem wyniku, użyj dwóch osobnych bloków UoW.
- Phase 1: załaduj agregat, ustaw status "in-progress", commituj (zwolnij transakcję).
- Phase 2: po długiej operacji, przeładuj agregat (wersja mogła się zmienić), zapisz wynik, commituj.

```python
async def handle(self, command: ProcessWorkflowCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(command.workflow_id)
        workflow.mark_processing()
        await unit_of_work.save(WorkflowRepository, workflow)

    result = await self._external_service.run(workflow.id)

    async with self._unit_of_work as unit_of_work:
        workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(command.workflow_id)
        workflow.complete(result)
        await unit_of_work.save(WorkflowRepository, workflow)
```

## Lokalizacja

- Port: `shell/platform/application/ports/persistence/unit_of_work.py`
- Baza implementacji: `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`
- Modele dostarczania (outbox/inbox): `shell/platform/infrastructure/persistence/sql/models/event_delivery.py` i `command_delivery.py`
