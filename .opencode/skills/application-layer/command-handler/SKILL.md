---
name: command-handler
description: Zasady budowy handlerów komend (Command Handlers) — struktura, lokalizacja, rejestracja. Używaj gdy dodajesz nowy command handler, poprawiasz istniejący, albo review'ujesz poprawność handlerów komend.
---

# Command Handler — obsługa komend

## Definicja

Command Handler to komponent warstwy aplikacyjnej, który przyjmuje komendę (Command), wykonuje operację biznesową na **dokładnie jednym agregacie** i zwraca wynik.

## Zasady

1. **Jeden handler = jeden agregat** — handler może modyfikować maksymalnie jeden agregat domenowy.
2. **Handler buduje agregat z repozytorium** — ładuje istniejący agregat lub tworzy nowy przez factory.
3. **Serwisy domenowe przez porty w module agregatu** — wszystko czego agregat potrzebuje do decyzji jest dostarczane przez serwisy, których porty są zdefiniowane w module agregatu.
4. **Wywołanie metody agregatu z kompletem parametrów** — handler woła metodę agregatu przekazując wszystkie dane (również te pobrane przez serwisy).
5. **Zapis + eventy w tej samej transakcji** — po wywołaniu metody agregatu: `save` + `stage_events`.
6. **Zero decyzji biznesowych** — handler nie zawiera `if/else` z logiką biznesową. Może rzucić jedynie błędem infrastrukturalnym lub domenowym.

## Lokalizacja

Handlery komend znajdują się w katalogu `shell/<service>/application/<bounded_context>/<aggregate>/command_handlers/`.

```
shell/<service>/application/
    execution/
        node_execution/
            command_handlers/
                create_node_execution_handler.py
                delete_node_execution_handler.py
        edge_execution/
            command_handlers/
                create_edge_execution_handler.py
                change_edge_execution_handler.py
        workflow/
            command_handlers/
                create_workflow_handler.py
                change_workflow_handler.py
    user/
        auth_session/
            command_handlers/
                login_auth_session_handler.py
    project/
        project/
            command_handlers/
                create_project_handler.py
                change_project_handler.py
                delete_project_handler.py
```

## Rejestracja

Rejestracja odbywa się w kontenerze DI danego BC (`shell/<service>/bootstrap/<bc>/container/<bc>_core_container.py`) — każdy handler ma provider `*_handler_factory = providers.Factory(...)` (patrz `handler-registration-integrity`).

> Szczegółowe reguły struktury → [command-handler-structure](../../pattern-standards/command-handler-structure/SKILL.md)
