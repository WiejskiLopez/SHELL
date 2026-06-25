---
name: command-handler
description: Zasady budowy handlerów komend (Command Handlers) — struktura, lokalizacja, rejestracja. Używaj gdy dodajesz nowy command handler, poprawiasz istniejący, albo review'ujesz poprawność handlerów komend.
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

## Rejestracja

Rejestracja odbywa się w kontenerze DI (dependency_injection) lub przez bezpośrednie wstrzyknięcie w warstwie framework/bootstrap.
