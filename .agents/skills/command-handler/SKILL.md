---
name: command-handler
description: Zasady budowy handlerów komend (Command Handlers) — nazewnictwo, struktura, lokalizacja, rejestracja. Używaj gdy dodajesz nowy command handler, poprawiasz istniejący, albo review'ujesz poprawność handlerów komend.
---

# Command Handler — obsługa komend

## Definicja

Command Handler to komponent warstwy aplikacyjnej, który przyjmuje komendę (Command), wykonuje operację biznesową na agregacie i zwraca wynik.

## Lokalizacja

Handlery komend znajdują się w katalogu `application/<bounded_context>/command_handlers/`.

```
shell/application/
    execution/
        command_handlers/
            start_workflow_handler.py
            import_task_execution_handler.py
            session_handlers/
                open_session_handler.py
                close_session_handler.py
    definition/
        command_handlers/
            index_document_handler.py
            bootstrap_runner_config_handler.py
```

## Nazewnictwo

```
Plik:  <command_name>_handler.py
Klasa: <CommandName>Handler
```

Przykłady:
- `StartWorkflowCommand` → plik `start_workflow_handler.py` → klasa `StartWorkflowHandler`
- `ImportTaskExecutionCommand` → plik `import_task_execution_handler.py` → klasa `ImportTaskExecutionHandler`

## Struktura handlera

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork

class StartWorkflowHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, logger: Logger) -> None:
        self._uow = uow
        self._clock = clock
        self._logger = logger

    async def handle(self, command: StartWorkflowCommand) -> None:
        async with self._uow as uow:
            workflow = Workflow.start_at(
                id_=self._id_gen.new_workflow_id(),
                session_id=command.session_id,
                now=self._clock.now(),
            )
            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
```

## Zasady

1. **Jeden handler = jedna komenda** — nigdy nie obsługuj wielu komend w jednym handlerze
2. **Stateless** — handler nie przechowuje stanu między wywołaniami
3. **stage_events(pull_events())** po każdej mutacji agregatu
4. **Porty w TYPE_CHECKING** — zależności infrastrukturalne wstrzykiwane przez DI
5. **Nazwa klasy = `<CommandName>Handler`** — musi korespondować z komendą
6. **Nazwa pliku = `<command_name>_handler.py`**
7. **Handler woła tylko metody biznesowe** na agregatach, nigdy techniczne (save, update, merge)

## Rejestracja

Rejestracja odbywa się w kontenerze DI (dependency_injection) lub przez bezpośrednie wstrzyknięcie w warstwie framework/bootstrap.
