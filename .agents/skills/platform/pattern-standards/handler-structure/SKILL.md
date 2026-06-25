---
name: handler-structure
description: Reguły struktury handlerów — bezstanowość, UoW jako context manager, stage_events, zakaz logiki biznesowej.
---

# Handler Structure

> Wspólne reguły struktury wszystkich handlerów (command, query, event) we wszystkich bounded contextach.

## Definicja

- Handler to komponent warstwy aplikacyjnej, który odbiera komendę/zapytanie/event i koordynuje wykonanie.

## Jeden handler = jeden typ

- Jeden handler obsługuje dokładnie jeden typ komendy/zapytania/eventu.
- Command/Query bus: mapowanie 1:1 typu na handler.
- Event bus: 1:N (jeden event może mieć wielu subskrybentów), ale każdy subskrybent pozostaje 1:1 z typem eventu.

```python
class StartWorkflowHandler:
    def __init__(self, ...) -> None:
        ...

    async def handle(self, start_workflow_command: StartWorkflowCommand) -> None:
        ...
```

## Metoda handle

- Pojedyncza publiczna metoda `async handle(self, command/query/event) -> None | DTO`.
- Typ przyjmowany: konkretna komenda/zapytanie/event.
- Typ zwracany: `None` dla command/event, DTO/read model dla query.

## Stateless

- Handler nie przechowuje stanu między wywołaniami.
- Wszystkie dane pochodzą z parametrów lub repozytoriów.
- Jedynymi polami instancji są wstrzyknięte zależności (porty).

## DI

- Zależności wstrzykiwane przez konstruktor.
- Porty/Protocol w TYPE_CHECKING.
- Import eventu/komendy w sekcji głównej — handler jawnie deklaruje co obsługuje.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.base import UnitOfWork

if TYPE_CHECKING:
    from shell.domain.workflow.repository import WorkflowRepository
```

## Lokalizacja

- Command handlers: `shell/application/<bc>/command_handlers/`
- Query handlers: `shell/application/<bc>/query_handlers/`
- Event handlers: `shell/application/<bc>/event_handlers/`
