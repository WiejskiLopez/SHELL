# Analiza 12 nieprzechodzących testów architektonicznych

**Data:** 2026-06-26
**Projekt:** SHELL (Python, Clean Architecture + DDD + Hexagonal + CQRS)
**Framework testowy:** pytest 9.0.2 + pytest-asyncio 1.4.0

**W skrócie:** 287 passed, 6 skipped, 8 xfailed, 3 xpassed, **12 failed**
Wszystkie 12 błędów to testy **architektoniczne** (lint-like). Zero błędów w testach funkcjonalnych (jednostkowych, integracyjnych, e2e).

---

## 🔴 Testy SŁUSZNE — należy naprawić kod źródłowy (7 testów)

### #1 `test_mutating_methods_emit_events` (test_domain_structure.py)

**Reguła:** Każda publiczna metoda mutująca w AggregateRoot musi wołać `append_event()`.

**Zgodność z DDD:** KRYTYCZNA — bez tego eventy domenowe są gubione, a workflowy zależne od event-driven orchestration psują się po cichu.

**Naruszenia (37 metod):**

| Agregat | Metody |
|---------|--------|
| `SchedulerDefinition` | `matches_trigger` (to query → dodać do wyjątków) |
| `AgentConfigExecution` | `update_config` |
| `Envelope` | `archive` |
| `GraphExecution` | `mark_verifying`, `suspend`, `resume`, `create_main_round`, `create_sub_graph` |
| `GraphExecutionState` | `get`, `patch`, `clear`, `merge`, `snapshot`, `supersede` |
| `GraphNodeExecutionState` | `get`, `patch`, `clear`, `snapshot` |
| `GraphNodeTransitionExecution` | `create_sequence`, `create_conditional`, `create_loop`, `create_spawn_subgraph`, `create_error_handler`, `create_timeout`, `create_default`, `skip` |
| `SessionState` | `get`, `patch`, `clear`, `snapshot` |
| `TaskExecution` | `increment_cycle`, `add_state_input`, `add_state_output`, `rename`, `execute_in_workflow`, `prepare_workspace` |
| `TaskExecutionState` | `supersede` |

**Zalecenie:**
- Dodać wywołania `append_event()` do każdej metody mutującej
- `SchedulerDefinition.matches_trigger` dodać do `_NON_MUTATING` (to metoda query, nie mutacja)
- Factory `create_*` (`classmethod`) są dyskusyjne — zazwyczaj event emituje caller; można dodać do `_KNOWN_NO_EVENT_EMIT`

---

### #2 `test_mutating_methods_have_guard` (test_domain_structure.py)

**Reguła:** Każda metoda mutująca w encji/agregacie powinna zaczynać się od klauzuli strażnika (`if ... raise`).

**Zgodność z DDD:** Programowanie defensywne — dobra praktyka, umiarkowany priorytet.

**Naruszenia (~46 metod):** Podobny zestaw jak w #1.

**Zalecenie:**
- Dodać `matches_trigger` do `_NON_MUTATING`
- Factory `create_*` dodać do wyjątków (guard w `__init__`)
- Dla `Session.open`, `GraphExecution.mark_verifying/suspend/resume` — dodać guardy sprawdzające stan przed tranzycją

---

### #4 `test_aggregate_references_by_id_only` (test_domain_structure.py)

**Reguła:** Agregaty mogą trzymać tylko ID innych agregatów, nigdy bezpośrednie referencje obiektów.

**Zgodność z DDD:** KRYTYCZNA — fundamentalna zasada DDD dla utrzymania granic agregatów i spójności transakcyjnej.

**Naruszenia (3 prawdziwe):**

| Plik | Pole | Problem |
|------|------|---------|
| `domain/execution/aggregates/workflow/workflow.py` | `_skills: list[WorkflowSkill]` | Trzyma encje zamiast ID |
| `domain/execution/aggregates/workflow/workflow.py` | `_state_inputs: list[WorkflowStateInput]` | Trzyma encje zamiast ID |
| `domain/execution/aggregates/workflow/workflow.py` | `_state_outputs: list[WorkflowStateOutput]` | Trzyma encje zamiast ID |

**Fałszywe pozytywy testu:**
- `GraphNodeTransitionExecution._target_node_execution_id: GraphNodeExecutionId | None` — TO jest ID, ale test sprawdza tylko `endswith("Id")` i nie obsługuje `Union/Optional`
- `Workflow._status: WorkflowStatus` — TO jest ValueObject, ale test nie odróżnia VO od encji/agregatu

**Zalecenie:**
- **Kod źródłowy:** Zmienić `_skills`, `_state_inputs`, `_state_outputs` na `list[WorkflowSkillId]` itd.
- **Test:** Poprawić wykrywanie typów Union/Optional oraz ValueObject

---

### #5 `test_entity_aggregate_fields_have_domain_types` (test_domain_structure.py)

**Reguła:** Pola encji/agregatów muszą używać typów domenowych (ValueObject), nie typów prymitywnych.

**Zgodność z DDD:** Zwalczanie primitive obsession — dobra praktyka.

**Naruszenie (1):**

| Plik | Pole | Jest | Ma być |
|------|------|------|--------|
| `domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py:22` | `_created_at` | `datetime` | `CreatedAt` |

**Zalecenie:** Zmiana jednej linii — `CreatedAt` już istnieje jako VO używane w innych agregatach (np. `Workflow._created_at: CreatedAt`).

---

### #7 `test_framework_does_not_import_infrastructure` (test_enterprise_patterns.py)

**Reguła:** Warstwa `framework/` nie może importować z `infrastructure/`.

**Zgodność z architekturą:** KRYTYCZNA — naruszenie zależności w layered/hexagonal architecture.

**Naruszenia (3):**

| Plik | Import | Problem |
|------|--------|---------|
| `framework/platform/cli/main.py:14` | `from shell.infrastructure... import ShellConfig` | Używane w runtime — **prawdziwe naruszenie** |
| `framework/execution/orchestration/sync_workflow_runner.py:27` | `from shell.infrastructure... import OutboxToInboxRelay` | Tylko TYPE_CHECKING — **fałszywy pozytyw** |
| `framework/execution/orchestration/sync_workflow_runner.py:28` | `from shell.infrastructure... import InboxProcessor` | Tylko TYPE_CHECKING — **fałszywy pozytyw** |

**Zalecenie:**
- **Kod:** `ShellConfig` wstrzyknąć przez port aplikacyjny zamiast bezpośredniego importu
- **Test:** Exemptować importy pod `TYPE_CHECKING` — nie są ewaluowane w runtime

---

### #8 `test_all_repository_ports_have_in_memory` (test_enterprise_patterns.py)

**Reguła:** Każdy port repozytorium musi mieć implementację InMemory.

**Zgodność z architekturą:** Testowalność — ważne dla unit testów bez bazy danych.

**Brakujące (4):**

| Brakujący plik | Port |
|----------------|------|
| `in_memory_agent_skill_execution_repository.py` | `AgentSkillExecutionRepository` |
| `in_memory_graph_execution_state_repository.py` | `GraphExecutionStateRepository` |
| `in_memory_session_state_repository.py` | `SessionStateRepository` |
| `in_memory_task_execution_state_repository.py` | `TaskExecutionStateRepository` |

**Zalecenie:** Stworzyć 4 pliki w `infrastructure/.../persistence/memory/` wzorując się na istniejących InMemory repo (np. `in_memory_graph_execution_repository.py`).

---

### #10 `test_infra_mappers_have_both_directions` (test_mapper_structure.py)

**Reguła:** Każdy mapper infrastruktury musi mieć funkcje `to_domain`/`to_entity` i `to_model`.

**Naruszenie (1):**

| Plik | Problem |
|------|---------|
| `infrastructure/definition/persistence/sql/mappers/graph_definition_mapper.py` | Ma tylko `graph_definition_model_to_dto` (model→DTO). Brak `model→entity` i `entity→model`. |

**Zalecenie:** Dodać funkcje mapowania w obie strony między `GraphDefinitionModel` a `GraphDefinition`.

---

## 🟡 Testy DYSKUSYJNE — test lub kod do poprawy (4 testy)

### #3 `test_domain_services_are_stateless` (test_domain_structure.py)

**Reguła:** Serwisy domenowe muszą być bezstanowe (tylko wstrzyknięte zależności).

**Problem:** `SubGraphExecutionService` zgłasza 9 pól (`_clock`, `_definition_provider`, `_governance`, `_id_generator`, `_logger`, `_observer`, `_security`, `_unit_of_work`, `_versioning`), ale WSZYSTKIE to wstrzyknięte zależności (porty). Heurystyka testu sprawdza czy pole kończy się `_` (underscore suffix) — żadne z tych pól nie ma trailing underscore.

**Zalecenie:** Dodać `SubGraphExecutionService` do `_KNOWN_SVC_STATEFUL`. Heurystyka testu jest za prosta by odróżnić "wstrzyknięty port" od "mutowalnego stanu".

---

### #6 `test_domain_event_fields_have_domain_types` (test_domain_structure.py)

**Reguła:** Pola DomainEvent muszą używać ValueObject, nie prymitywów (`str`/`dict`/`list`/`Any`).

**Problem:** Eventy domenowe są serializowane do JSON (outbox), więc używanie str jest naturalne na granicy systemu.

**Naruszenia (4 eventy, 11 pól):**

| Event | Pole | Problem |
|-------|------|---------|
| `SessionStateChangedEvent` | `session_id: str` | Powinno być `SessionId` |
| `SessionStateChangedEvent` | `session_state_id: str` | Powinno być `SessionStateId` |
| `SessionStateChangedEvent` | `kind: str` | Dyskusyjne — dane serializowane |
| `SessionStateChangedEvent` | `key: str` | Dyskusyjne — dane serializowane |
| `GraphNodeExecutionStateChangedEvent` | `graph_node_execution_id: str` | Powinno być `GraphNodeExecutionId` |
| `GraphNodeExecutionStateChangedEvent` | `graph_node_execution_state_id: str` | Powinno być `GraphNodeExecutionStateId` |
| `GraphNodeExecutionStateChangedEvent` | `kind: str` | Dyskusyjne |
| `GraphNodeExecutionStateChangedEvent` | `key: str` | Dyskusyjne |
| `GraphNodeExecutionCompletedEvent` | `result_id: str \| None` | Powinno być `GraphNodeExecutionResultId \| None` |
| `GraphExecutionConstructedEvent` | `graph_execution_id: str` | Powinno być `GraphExecutionId` |
| `GraphExecutionConstructedEvent` | `task_execution_id: str` | Powinno być `TaskExecutionId` |

**Zalecenie:**
- ID → zmienić na właściwe VO (większość już istnieje)
- `kind`, `key` → dodać do listy wyjątków testu (albo owinąć w VO `StateKind`)

---

### #9 `test_init_files_only_re_export` (test_general_conventions.py)

**Reguła:** `__init__.py` powinno tylko re-exportować, nie definiować klas/funkcji.

**Problem:** Reguła słuszna dla `domain/` i `application/`, ale w `infrastructure/` i `framework/` `__init__.py` często zawiera implementacje — to naturalne dla płytkich pakietów i FastAPI routerów.

**Naruszenia (główne):**

| Plik | Zawartość |
|------|-----------|
| `infrastructure/platform/logging/__init__.py` | Klasa `StdlibLogger` z metodami |
| `infrastructure/platform/time/__init__.py` | `SystemClock`, `UuidIdGenerator`, factory functions |
| `infrastructure/platform/persistence/sql/__init__.py` | `build_session_factory`, `run_migrations` |
| `infrastructure/platform/persistence/sql/mappers/__init__.py` | 70+ funkcji mapperów (889 linii) |
| `framework/execution/api/routers/task_executions/__init__.py` | FastAPI endpoint functions |
| `framework/execution/api/routers/workflows/__init__.py` | FastAPI endpoint functions |

**Zalecenie:**
- Ograniczyć regułę tylko do warstw `domain/`, `application/`, `bootstrap/`
- Dodać znane wyjątki dla `infrastructure/` i `framework/`
- Rozważyć podział `mappers/__init__.py` na osobne pliki (889 linii to problem utrzymaniowy)

---

### #12 `test_no_abbreviations_in_function_names` (test_naming_conventions.py)

**Reguła:** Nazwy funkcji/metod nie mogą używać skrótów.

**Problem:** Czarna lista (`_KNOWN_ABBREVIATIONS`) zawiera wyrazy które są powszechnie przyjętymi akronimami, nie skrótami.

**Naruszenia (~29 funkcji):**

| Skrót w czarnej liście | Liczba naruszeń | Analiza |
|------------------------|-----------------|---------|
| `dto` | ~15 | **Akronim, nie skrót** — DTO (Data Transfer Object) to standardowy termin w DDD/Clean Architecture |
| `config` | ~8 | **Akronim, nie skrót** — używany nawet w stdlib (`configparser`) |
| `args` | 1 | **Standard CLI** — `parse_args` to uniwersalny wzorzec (argparse) |

**Prawdziwe skróty (zostawić w czarnej liście):** `repo` → `repository`, `cmd` → `command`, `uow` → `unit_of_work`, `ctx` → `context`

**Zalecenie:** Usunąć `dto`, `config`, `args` z `_KNOWN_ABBREVIATIONS`.

---

## 🔴🔴🔴 Test BŁĘDNY — wymaga gruntownej przeróbki (1 test)

### #11 `test_filename_matches_class_name` (test_naming_conventions.py)

**Reguła:** Nazwa pliku powinna odpowiadać nazwie głównej klasy (PascalCase → snake_case).

**Problem:** Test produkuje ~107 fałszywych pozytywów przez błędną heurystykę.

**Główne problemy:**

| Problem | Przykład | Wyjaśnienie |
|---------|----------|-------------|
| Pliki testowe | `test_outbox.py → TestInMemoryOutboxStore` | Nazwa testu opisuje scenariusz, nie największą klasę |
| `__init__.py` | `__init__.py → dowolna klasa` | `__init__.py` nigdy nie będzie pasować |
| Pliki modeli | `graph_execution.py → GraphExecutionModel` | Plik nazwany od agregatu, klasa modelu to szczegół |
| Pliki z wieloma klasami | `ids.py → SchedulerDefinitionId` | Wiele klas ID w jednym pliku |
| Pliki portów | `identity.py → IdGenerator` | Plik nazwany od konceptu, nie klasy |
| Bug w _SOFT_AREAS | `/tests/` nie matchuje `tests/...` (brak leading `/`) | Testy nie są poprawnie wykluczone |

**Zalecenie:** Gruntowna przeróbka:
1. Poprawić `_SOFT_AREAS` by poprawnie wykluczać katalog `tests/`
2. Wykluczyć `__init__.py`
3. Wykluczyć pliki modeli (`xxx.py` → `XxxModel`)
4. Wykluczyć `value_objects/ids.py`
5. Zmienić heurystykę: zamiast "największa klasa → nazwa pliku", sprawdzać "CZY JAKAKOLWIEK klasa pasuje do nazwy pliku"
6. Opcjonalnie: zawęzić tylko do `domain/` i `application/`

---

## Proponowana kolejność napraw

### Faza 1 — Quick wins (łatwe, natychmiastowy efekt)
1. **#5** — `AgentSkillExecution._created_at`: `datetime` → `CreatedAt` (1 linia)
2. **#12** — Usunąć `dto`, `config`, `args` z `_KNOWN_ABBREVIATIONS`
3. **#8** — Stworzyć 4 InMemory repos (mechaniczna robota, wzorować się na istniejących)

### Faza 2 — Architektoniczne (kluczowe dla zgodności z DDD)
4. **#7** — Usunąć bezpośredni import `ShellConfig` z `main.py` (wstrzyknąć przez port); exemptować TYPE_CHECKING
5. **#4** — Poprawić `Workflow._skills/_state_inputs/_state_outputs` na ID; poprawić test (Union/Optional/VO)
6. **#1** — Dodać `append_event()` do metod mutujących (37 metod — największa zmiana)

### Faza 3 — Mapowanie i serwisy
7. **#10** — Dodać brakujące kierunki w `graph_definition_mapper.py`
8. **#3** — Dodać `SubGraphExecutionService` do `_KNOWN_SVC_STATEFUL`

### Faza 4 — Poprawki testów (wymagają decyzji projektowych)
9. **#6** — Event field types: ID → VO + wyjątki dla `kind`/`key`
10. **#9** — `__init__.py`: ograniczyć regułę do `domain/`/`application/`/`bootstrap/`
11. **#2** — Guard clauses (najniższy priorytet biznesowy)
12. **#11** — Gruntowna przeróbka testu filename-matches-classname

---

## Podsumowanie

| # | Test | Typ problemu | Cel naprawy | Priorytet |
|---|------|-------------|-------------|-----------|
| 1 | `test_mutating_methods_emit_events` | 🔴 Kod źródłowy | Dodać eventy + wyjątki | Wysoki |
| 2 | `test_mutating_methods_have_guard` | 🔴 Kod źródłowy | Dodać guardy + wyjątki | Niski |
| 3 | `test_domain_services_are_stateless` | 🟡 Test | Dodać do _KNOWN_SVC_STATEFUL | Średni |
| 4 | `test_aggregate_references_by_id_only` | 🔴 Kod + Test | Workflow → ID; poprawić Union/VO | Wysoki |
| 5 | `test_entity_aggregate_fields_have_domain_types` | 🔴 Kod źródłowy | `datetime` → `CreatedAt` | Błyskawiczny |
| 6 | `test_domain_event_fields_have_domain_types` | 🟡 Kod + Test | ID → VO; wyjątki dla kind/key | Średni |
| 7 | `test_framework_does_not_import_infrastructure` | 🔴 Kod + Test | Port dla ShellConfig; exempt TYPE_CHECKING | Wysoki |
| 8 | `test_all_repository_ports_have_in_memory` | 🔴 Kod źródłowy | 4 nowe InMemory repos | Średni |
| 9 | `test_init_files_only_re_export` | 🟡 Test | Ograniczyć do domain/application | Niski |
| 10 | `test_infra_mappers_have_both_directions` | 🔴 Kod źródłowy | Dodać 2 funkcje mapowania | Średni |
| 11 | `test_filename_matches_class_name` | 🔴🔴🔴 Test | Gruntowna przeróbka | Wysoki |
| 12 | `test_no_abbreviations_in_function_names` | 🟡 Test | Usunąć dto/config/args z blacklisty | Średni |
