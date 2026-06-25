# Command Handler Structure

> Reguły struktury Command Handler (Application Service) we wszystkich bounded contextach.

## Definicja

- Command Handler koordynuje wykonanie komendy — nie zawiera logiki biznesowej.
- Odpowiada za: odebranie komendy, mapowanie na obiekty domenowe, autoryzację, walidację wejściową, koordynację domeny, zarządzanie transakcją (UoW), emitowanie eventów, mapowanie wyniku.

## Klasa

- Zależności wstrzykiwane przez konstruktor.
- Porty repozytoriów i serwisów w TYPE_CHECKING.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.workflow.repository import WorkflowRepository
    from shell.domain.platform.ports import UnitOfWork
```

## Metoda handle

- Pojedyncza `async handle(self, command: TCommand) -> None`.
- Komenda zmienia stan, zwraca None (lub ID utworzonego obiektu).

## Struktura metody

```python
async def handle(self, start_workflow_command: StartWorkflowCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        workflow = Workflow.create(
            workflow_id=WorkflowId.generate(),
            name=WorkflowName(start_workflow_command.name),
            owner_id=UserId(start_workflow_command.owner_id),
        )
        unit_of_work.workflow_repository.save(workflow)
        unit_of_work.stage_events(workflow.pull_events())
```

## Koordynacja, nie logika

- Handler koordynuje, nie zawiera logiki biznesowej.
- Jeśli w handlerze pojawia się `if/else` z regułami biznesowymi → przenieś do Domain Service lub agregatu.

```python
# Dobrze — delegacja do agregatu
workflow.start()

# Źle — logika biznesowa w handlerze
if workflow.status == 'idle':
    workflow.status = 'running'
    ...
```

## UoW

- `async with self._unit_of_work as unit_of_work:` — UoW jako async context manager.
- `commit()` na `__aexit__` jeśli brak wyjątku; `rollback()` jeśli wyjątek.
- Nigdy ręcznego `unit_of_work.commit()` w handlerze.
- `stage_events(aggregate.pull_events())` po każdej mutacji agregatu.

## Walidacja

- Strukturalna walidacja (typy, formaty, zakresy) przed przekazaniem do domeny.
- Biznesowa walidacja w domenie (VO, agregat).

## Lokalizacja

- `shell/application/<bc>/command_handlers/`

## Bezpieczeństwo

- Handler nie importuje infrastruktury.
