# Przegląd projektu SHELL pod kątem 3 koncepcji komunikacji międzyagregatowej (aktualizacja)

> Przegląd kodu (stan z dnia przeglądu) względem **aktualnej** wersji wzorców w skillach:
> - **Repository** — `repositories/` (persystencja własna).
> - **Aggregate Provider** — porty tylko-do-odczytu, nazwa `<Dane>Provider`.
> - **Command Port** — porty operacji/mutacji, nazwa `<Czasownik><Obiekt>Port`.
> - Porty wyjściowe agregatu żyją w **dwóch** katalogach domeny: `repositories/` i `ports/`
>   (Provider i Command Port **razem** w `ports/`, rozróżnia je **wyłącznie nazwa**).
> - Adaptery w infrastrukturze w **`adapters/<port_name>/`** (`*_http_adapter.py` cross-BC,
>   `*_sql_adapter.py` lokalny, plus `contracts/v1/` + `mappers/`).
> - Reguła kardynalna: **zero bezpośredniego wstrzykiwania** cudzego QueryService/Repository/serwisu
>   (także w obrębie tego samego BC).

---

## 1. Repository (`repositories/`) — w większości przestrzegane, 4 luki

### Zgodne ze wzorcem

- Porty repozytoriów w `domain/<bc>/aggregates/<agregat>/repositories/` — wszędzie.
- Adaptery SQL w `infrastructure/<bc>/<agregat>/persistence/sql/repositories/`.
- Adaptery InMemory w `infrastructure/<bc>/<agregat>/persistence/memory/`.
- Nazewnictwo `Sql<X>Repository` / `InMemory<X>Repository`.
- Generyczny `RepositoryPort[TAggregate, TId_co]` z platformy jest używany.
- Przykład wzorcowy: `graph_execution` — port + `sql_graph_execution_repository.py` + `in_memory_graph_execution_repository.py`.

### Naruszenia / luki

1. **Brak adaptera SQL dla 4 agregatów** — port + model ORM + InMemory istnieją, ale
   `persistence/sql/repositories/` jest **pusty**:
   - `execution_service/.../agent_config_execution`
   - `execution_service/.../agent_execution`
   - `execution_service/.../agent_skill_execution`
   - `session_service/.../session_state`
   Jeśli te agregaty mają przetrwać restart (mają ORM modele i migracje), to realna dziura
   w persystencji (InMemory działa w testach, w produkcji brak zapisu/odczytu SQL).

2. `agent_execution_repository.py` **redefiniuje metody** (`get_by_id`, `delete`, `exists`, `save`)
   zamiast rozszerzać generyczny `RepositoryPort` i ma niespójne nazwy parametrów (`id_` w
   `get_by_id` vs `id` w `delete`).

---

## 2. Provider (`<Dane>Provider`) — realizowany w duchu, zgodny katalog, 3 błędy jakości

### Zgodne z aktualnym wzorcem

- **Katalog `ports/` jest POPRAWNY** — od dziś Provider i Command Port żyją razem w `ports/`
  (to było wcześniej zgłaszane jako naruszenie; po zmianie w skillach przestaje nim być).
- **Wersjonowane kontrakty + mappery** w adapterach HTTP:
  `graph_execution/http/providers/graph_execution_definition/{contracts/v1/, mappers/}`,
  `session_execution/http/{contracts/v1/, mappers/}` — flow
  "remote response → consumer-local V1 → mapper → VO".
- **Zapytanie jako VO**: `graph_definition_semantic_query.py` — argument portu jako Value Object.
- **Adapter jedynym miejscem znającym źródło**: `SqlUserQueryProvider` opakowuje źródłowy
  `UserQueryService` (ten sam BC, agregat `user`).
- **Nazewnictwo adapterów** `<Port>HttpAdapter` i dziedziczenie po porcie — zgodne.
- **Wspólny klient HTTP** `platform/infrastructure/context/client.py` (`CorrelationIdAsyncClient`).

### Naruszenia / luki

1. **MUTACJA nazwana Provider** — `WorkflowSessionProvider.add_session_output()` wykonuje
   **HTTP POST** (tworzy/zapisuje output w execution BC) → to **Command Port**
   (`<Czasownik><Obiekt>Port`, np. `WorkflowSessionCommandPort`), nie Provider.
   Dodatkowo port jest **martwy**: zdefiniowany + adapter, ale nieużywany w kodzie produkcyjnym
   i **niezarejestrowany w DI**. Sygnatura używa typów prostych
   (`session_id: str`, `user_id: str`, `payload: dict[str, Any]`).

2. **Provider zwraca AGGREGAT zamiast VO/read modelu** — `UserQueryProvider.get_by_email() -> User`
   zwraca pełny agregat `User`. `LoginAuthSessionHandler` sięga w `user.id`, `user.status`,
   `user.email` → coupling konsumenta do kształtu obcego agregatu. Powinno zwracać minimalny
   snapshot/VO konsumenta (np. `UserSnapshot { id, status }`).

3. **Typy proste w sygnaturach portów** (narusza regułę domain port signatures):
   - `SessionQueryProvider.get_by_id(session_id: str)`
   - `GraphExecutionDefinitionProvider.get_graph_definition(definition_id: str)` (i po semantic)
   - `WorkflowSessionProvider(... str, str, dict)`
   Powinny być VO/ID (np. `SessionId`, `GraphDefinitionReferenceId`).

4. **Lokalizacja adapterów odbiega od `adapters/<port_name>/`**:
   - `http/providers/<nazwa>/` — `graph_execution` (poprawna struktura per-port, ale ścieżka przez `http/providers/`)
   - bezpośrednio `http/` — `session_execution`, `session_service` (workflow_session_provider)
   - stary wzorzec `services/` — `infrastructure/user/auth_session/services/user_query_provider.py`,
     `.../services/secure_token_generator.py`
   Docelowo: `infrastructure/<bc>/<aggregate>/adapters/<port_name>/`.

---

## 3. Command Port (`<Czasownik><Obiekt>Port`) — koncepcja NIEREALIZOWANA

- **Brak jakiegokolwiek portu operacyjnego/mutującego.** Katalogi `ports/` zawierają wyłącznie
  providerów albo są puste.
- Jedyny kandydat to `WorkflowSessionProvider.add_session_output` (mutacja) — błędnie nazwany
  Provider i martwy (punkt 2.1). Po aktualnym wzorcu to powinien być `WorkflowSessionCommandPort`
  w `ports/` z adapterem w `adapters/workflow_session_command_port/`.
- Cała komunikacja cross-BC to **3 adaptery HTTP, wszystkie tylko-odczyt**
  (`graph_execution_definition_provider`, `session_query_provider`, `workflow_session_provider`).
  Żadnej synchronicznej mutacji cross-BC nie modeluje się przez port operacyjny.
- Granica sync/async ze wzorca nie ma pokrycia w kodzie: brak portów operacyjnych do porównania
  z eventami/sagami.

---

## 4. Reguła kardynalna (zero bezpośredniego wstrzykiwania) — przestrzegana z 1 wyjątkiem

### Zgodne

- `LoginAuthSessionHandler` wstrzykuje porty (`UserQueryProvider`, `TokenGenerator`), a nie
  `UserQueryService`/`UserRepository` bezpośrednio.
- `SqlUserQueryProvider` jest jedynym miejscem które zna źródłowy `UserQueryService` (ten sam BC).
- Arch-test `test_cross_aggregate_discipline__test_*_handlers_dont_use_cross_bc_repos.py` blokuje
  sięganie po repozytoria innych BC.

### Naruszenie / ryzyko

- **Coupling przez typ zwrotny providera**: mimo portu, `LoginAuthSessionHandler` zależy od pełnego
  agregatu `User` (punkt 2.2). Port istnieje, ale kontrakt przepuszcza agregat → granica autonomii
  rozszczelniona.
- Arch-testy sprawdzają tylko cross-BC; reguła "też w obrębie tego samego BC" nie ma testu.

---

## 5. Artefakty do decyzji (niekoniecznie naruszenia)

- **13 pustych katalogów `ports/`** w domenie (tylko `__init__.py`), np.
  `agent_config_execution/ports`, `node_execution/ports`, `workflow/ports`, `task_execution/ports`
  i inne — artefakt scaffoldu. Po aktualnym wzorcu `ports/` jest katalogiem docelowym dla
  providerów i portów operacyjnych, więc puste katalogi są albo do wypełnienia, albo do usunięcia.
- **Porty na poziomie BC** (nie agregatu): `session_service/domain/session/ports/`,
  `user_service/domain/user/ports/` — wzorzec przewiduje porty per agregat.

---

## 6. Plan napraw (wg aktualnych wzorców)

| # | Problem | Plan naprawy | Priorytet |
|---|---------|--------------|-----------|
| 1 | `WorkflowSessionProvider.add_session_output` = mutacja nazwana Provider; martwy | Przemodelować na Command Port: `WorkflowSessionCommandPort` w `ports/`, adapter `adapters/workflow_session_command_port/*_http_adapter.py`, zarejestrować w DI (lub usunąć, jeśli nieużywany) | wysoki |
| 2 | Provider zwraca agregat (`User`) zamiast VO/read modelu | `UserQueryProvider.get_by_email() -> UserSnapshot` (VO konsumenta); `LoginAuthSessionHandler` używa snapshotu | wysoki |
| 3 | Typy proste w sygnaturach portów | Zamienić na VO/ID (`SessionId`, `GraphDefinitionReferenceId` itd.) | średni |
| 4 | Brak adapterów SQL dla 4 agregatów | Dodać `sql_*_repository.py` dla `agent_config_execution`, `agent_execution`, `agent_skill_execution`, `session_state` (lub jawnie zadecydować, że to agregaty transient/read-only bez persystencji) | średni |
| 5 | Niespójne lokalizacje adapterów | Przenieść do `infrastructure/<bc>/<aggregate>/adapters/<port_name>/` (`*_http_adapter.py`, `*_sql_adapter.py`, `contracts/v1/`, `mappers/`); wycofać `http/providers/`, `http/`, `services/` jako lokalizacje adapterów | średni |
| 6 | `agent_execution_repository` redefiniuje metody bazy + `id_`/`id` | Rozszerzyć `RepositoryPort`, ujednolicić parametry | niski |
| 7 | Puste `ports/` (13 szt.) i porty na poziomie BC | Decyzja: wypełnić pod realne porty albo usunąć puste katalogi; porty BC przenieść do agregatu | decyzja |
| 8 | Reguła same-BC bez testu | Rozszerzyć `test_cross_aggregate_discipline` o blokadę bezpośredniego wstrzykiwania w obrębie BC | średni |
