# Do usunięcia — martwy kod po refaktorze kontenerów (Pure DI)

Lista elementów, które według mnie **nie są używane** i można bezpiecznie usunąć
po refaktorze Composition Root z `dependency-injector` na Pure DI.

## 1. Martwe kontenery `dependency-injector` per BC

Nikt ich nie importuje (potwierdzone grepem — jedyną referencją był `README.md`,
który już został zaktualizowany):

- `shell/bootstrap/user/container/user_core_container.py`
- `shell/bootstrap/session/container/session_core_container.py`
- `shell/bootstrap/execution/container/execution_core_container.py`
- `shell/bootstrap/definition/container/definition_core_container.py`

Po usunięciu warto usunąć także puste katalogi
`shell/bootstrap/{user,session,execution,definition}/container/`.

> Uwaga: `shell/bootstrap/execution/container/` NIE jest tym samym co
> `shell/bootstrap/execution/cli/` i `shell/bootstrap/execution/factory/`
> (`ApplicationFactory` — ŻYWE, zostają).

## 2. Zależność `dependency-injector`

Jedynymi użyciami `dependency_injector` w kodzie były kontenery z punktu 1
(poza stringami w testach architektury). Po ich usunięciu:

- Usuń `"dependency-injector>=4.49.1"` z `pyproject.toml` (sekcja `[project].dependencies`, linia 13).
- Usuń `"dependency_injector.*"` z `[[tool.mypy.overrides]]` w `pyproject.toml` (linia 108).
- Przebuduj lockfile: `uv lock && uv sync` (regeneracja `uv.lock`).

## 3. Nieużywane shimy kompatybilności w platform/bootstrap/container/

- `shell/platform/bootstrap/container/commands.py`
- `shell/platform/bootstrap/container/queries.py`

Te pliki tylko re-eksportują `Commands` / `Queries`, ale **nikt ich nie importuje**
(grep nie znajduje żadnego `container.commands` / `container.queries`).
Prawdziwe definicje mieszkają w `command_factories.py` / `query_factories.py`
i są eksportowane z `__init__.py`.

> Jeśli celowo trzymasz je jako stabilne ścieżki importu dla zewnętrznych narzędzi
> — zostaw, ale wtedy usuń ten punkt.

## 4. Redundantne override'y metod w `Commands`

W `shell/platform/bootstrap/container/command_factories.py` klasy `Commands`
nadpisuje 17 metod tylko po to, żeby zawołać `super().metoda()` — dziedziczenie
po mixinach `ExecutionCommandFactories` i `SchedulingCommandFactories` już to
zapewnia. Te metody są czystym boilerplate'em:

- `delete_node_execution_handler_factory`
- `create_node_execution_handler_factory`
- `create_edge_execution_handler_factory`
- `update_edge_execution_handler_factory`
- `delete_edge_execution_handler_factory`
- `create_edge_link_execution_handler_factory`
- `delete_edge_link_execution_handler_factory`
- `update_edge_link_execution_handler_factory`
- `create_scheduler_definition_handler_factory`
- `update_scheduler_definition_handler_factory`
- `delete_scheduler_definition_handler_factory`
- `create_scheduler_execution_handler_factory`
- `update_scheduler_execution_handler_factory`
- `delete_scheduler_execution_handler_factory`
- `create_scheduler_job_handler_factory`
- `update_scheduler_job_handler_factory`
- `delete_scheduler_job_handler_factory`

Usunięcie tych override'ów nie zmienia zachowania — `commands.XYZ_factory`
nadal rozwiązuje się do metody mixina.

---

## Weryfikacja po zmianach

```powershell
# 1. Cały stack kontenerów wciąż się buduje i wiąże busy
python -c "
from shell.platform.bootstrap.container.core_container import Container
from shell.platform.bootstrap.factory.bus_factory import wire_buses
c = Container(db_url='sqlite+aiosqlite:///:memory:')
wire_buses(c)
print('OK')
"

# 2. Testy
python -m pytest shell/tests -x -k "container or architecture"
```
