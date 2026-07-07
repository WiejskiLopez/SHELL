# Podsumowanie prac — branch `21-poprawa-handlerow`

Data: 2026-07-07

---

## 1. Analiza architektury

Przeprowadzono pełną analizę rozdzielenia funkcjonalności na warstwy wg wzorca:
- `platform/` — elementy wspólne platformowe (dla wszystkich modułów)
- `<moduł>/<agregat>/` — elementy per-agregat we wszystkich warstwach

---

## 2. P1 — Usunięcie duplikatów portów query (application layer)

### Problem
W `application/platform/ports/queries/` znajdowało się 6 portów query service, które były **zduplikowane** — identyczne pliki istniały już w lokalizacjach per-agregat.

### Zmiany

**Usunięte pliki (legacy):**
- `application/platform/ports/queries/session_query_service.py`
- `application/platform/ports/queries/task_execution_query_service.py`
- `application/platform/ports/queries/workflow_query_service.py`
- `application/platform/ports/queries/node_execution_result_query_service.py`
- `application/platform/ports/queries/runner_config_query_service.py`
- `application/platform/ports/queries/rag_query_service.py`

**Zaktualizowany** `application/platform/ports/queries/__init__.py` — pozostał tylko `MessageQueryService` (Message to agregat platformowy).

**7 handlerów z aktualizacją importów** (z `platform.ports.queries` → właściwe per-agregat porty):
- `execution/session_execution/query_handlers/session_get_history_handler.py`
- `execution/node_execution/query_handlers/node_execution_get_result_handler.py`
- `execution/task_execution/query_handlers/task_execution_get_by_name_handler.py`
- `execution/task_execution/query_handlers/task_execution_get_current_handler.py`
- `execution/workflow/query_handlers/workflow_get_by_id_handler.py`
- `definition/rag_document/query_handlers/rag_search_similar_handler.py`
- `definition/runner_config/query_handlers/runner_config_get_handler.py`

---

## 3. P2 — Usunięcie pustych legacy shells

### Usunięte puste katalogi infrastruktury (stare top-level dirs zastąpione przez `<moduł>/<agregat>/`):

| Katalog | Powód |
|---|---|
| `infrastructure/user/http/` | pusty |
| `infrastructure/session/http/` | pusty |
| `infrastructure/user/persistence/memory/` | pusty |
| `infrastructure/execution/persistence/memory/` | pusty (re-export bez importerów) |
| `infrastructure/execution/default_implementations/` | pusty |
| `infrastructure/session/persistence/sql/models/base.py` | nieużywany `Base(DeclarativeBase)` |
| `infrastructure/user/persistence/sql/models/base.py` | nieużywany `Base(DeclarativeBase)` |
| `infrastructure/user/persistence/sql/models/_compat.py` | nieużywany |
| `infrastructure/project/persistence/sql/models/base.py` | nieużywany `Base(DeclarativeBase)` |

### Usunięty pusty katalog application:
- `application/session/command_handlers/session_handlers/` — zawierał tylko `SKILL.md` i `__init__.py`; prawdziwe handlery są w `application/session/session/command_handlers/`

### Usunięte pliki SKILL.md z katalogów kodu źródłowego:
- `application/platform/event_handlers/SKILL.md`
- `application/execution/event_handlers/SKILL.md`
- `infrastructure/platform/persistence/sql/models/SKILL.md`

### Naprawa testu:
- `tests/execution/session_execution/integration/sql_sqlite/test_sql_session_repository.py` — zaktualizowany import `SessionOpenHandler` / `SessionCloseHandler` ze starej lokalizacji na `application/session/session/command_handlers/`

---

## 4. P3 — Rozbicie monolitycznych plików mapperów

### Problem
Każdy moduł (execution, user, session, project) miał jeden duży plik `infrastructure/<moduł>/persistence/sql/mappers/__init__.py` zawierający mappery dla **wszystkich** agregatów danego modułu.

### Rozwiązanie
Stworzono **17 per-agregatowych plików mapperów** w lokalizacji `<agregat>/persistence/sql/mappers.py`:

#### User BC (3 pliki)
- `infrastructure/user/user/persistence/sql/mappers.py`
- `infrastructure/user/user_skill/persistence/sql/mappers.py`
- `infrastructure/user/user_state/persistence/sql/mappers.py`

#### Session BC (1 plik)
- `infrastructure/session/session/persistence/sql/mappers.py`

#### Project BC (3 pliki)
- `infrastructure/project/project/persistence/sql/mappers.py`
- `infrastructure/project/project_skill/persistence/sql/mappers.py`
- `infrastructure/project/project_state/persistence/sql/mappers.py`

#### Execution BC (10 plików)
- `infrastructure/execution/task_execution/persistence/sql/mappers.py`
- `infrastructure/execution/task_execution_state/persistence/sql/mappers.py`
- `infrastructure/execution/graph_execution/persistence/sql/mappers.py`
- `infrastructure/execution/graph_execution_state/persistence/sql/mappers.py`
- `infrastructure/execution/workflow/persistence/sql/mappers.py`
- `infrastructure/execution/workflow_state/persistence/sql/mappers.py`
- `infrastructure/execution/user_execution/persistence/sql/mappers.py`
- `infrastructure/execution/user_execution_state/persistence/sql/mappers.py`
- `infrastructure/execution/session_execution/persistence/sql/mappers.py`
- `infrastructure/execution/session_execution_state/persistence/sql/mappers.py`

### 18 repozytoriów zaktualizowano importy
Każde repozytorium teraz importuje z własnego per-agregatowego pliku mapperów zamiast z centralnego `__init__.py`.

### 4 monolityczne `__init__.py` → cienkie re-exporty
Zachowano wsteczną kompatybilność (np. dla `tests/infrastructure/platform/test_mappers_round_trip.py`). Plik execution zmniejszył się z ~500 do 82 linii.

---

## 5. Co pozostało do zrobienia (P3 — przyszłe zadania)

- **`application/platform/ports/execution/`** — `NodeExecutionProcessRunner`, `NodeExecutionWorkspace` to porty specyficzne dla agregatu `node_execution`, a `TaskExecutionLoader` (`filesystem.py`) dla `task_execution`. Brak duplikatów — do przeniesienia.
- **Bootstrap** — `bootstrap/platform/container/infrastructure_container.py` zawiera rejestracje execution/definition-specific; można przenieść do `bootstrap/execution/` i `bootstrap/definition/`.

---

## Wynik końcowy

```
ruff check shell  → All checks passed!
pytest shell/tests (unit + arch + integration/sqlite) → PASSED (1 skipped — PG_TEST_URL not set)
```
