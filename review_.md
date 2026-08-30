# Code Review — SHELL (raport ustaleń)

Data: 2026-08-30
Zakres: cały monorepo `shell/` — 8 bounded contextów (`platform` + 7 × `*_service`), ~2400 plików produkcyjnych, ~1300 testów.
Metodyka: przegląd wykonany wg zestawu skilli `review-*` (`.opencode/skills/review/`); narzędzia uruchomione lokalnie (`ruff`, `import-linter`, `mypy --no-incremental` — wszystkie zakończone bez błędów **w aktualnej konfiguracji**), plus 6 równoległych przeglądów domenowych z weryfikacją najpoważniejszych ustaleń w źródłach.

Klasyfikacja wg `review-severity-levels`: **BLOCKER / CRITICAL / HIGH / MEDIUM / LOW / NIT**.

---

## Podsumowanie wykonawcze

Kod jest **architektonicznie czysty w warstwach, które przeszły do nowego modelu per-BC**: zero bezpośrednich importów między BC, zero importów infrastruktury/ORM w warstwie domeny, porty i adaptery poprawnie rozdzielone, UoW + outbox w jednej transakcji, idempotencja inbox, segregacja read/write (CQRS). To bardzo dobra baza.

Najpoważniejsze problemy leżą **nie w modelu domeny, lecz w granicach bezpieczeństwa i w mechanizmach, które mają chronić architekturę przed regresją**:

1. **Ekspozycja danych** — publiczny endpoint enumeracji użytkowników (`GET /users/by-email`) ujawnia, czy dany e-mail jest zarejestrowany, oraz zwraca powiązany `user_id`. (BLOCKER)
2. **Testy architektoniczne część próżna** — kluczowe strażniki (no-service-locator, framework→infra, domain imports) skanują nieistniejące katalogi, więc **nie mogą nigdy spaść**. (CRITICAL)
3. **Bramki CI są częściowo dekoracyjne** — próg pokrycia `--cov-fail-under=80` i Bandit uruchamiane z `-AllowFailure` (reguła zero-wyjątków); mypy nie jest uruchamiany w GitHub Actions. (CRITICAL/HIGH)
4. **Dziury w integracji** — niezarejestrowana komenda `DELETE /node-executions/{id}` (zawsze 500), nieistniejące typy `Identity/Time` ukryte `# type: ignore[attr-defined]`, synchronizacja InMemory↔SQL asymetryczna.
5. **Domena** — brak blokady soft-deleted w metodach FSM, fabrykowanie `graph_definition_id`, fałszowanie osi czasu w `*_state.change_state()`.

---

## Pozytywy (zweryfikowane, brak uwag)

- Kierunek zależności: `domain` nie importuje `infrastructure`/ORM; `application` zależy od portów (0 naruszeń w regex na wszystkich BC).
- Brak Service Locator / `container.resolve()` w kodzie biznesowym; DI per BC izolowane, UoW rejestrowany jako `providers.Factory` (nie singleton).
- Zdarzenia domenowe: frozen dataclass, nazwy w czasie przeszłym, emitowane w metodach domenowych.
- Transactional outbox poprawny (`SqlAlchemyUnitOfWorkBase._write_staged_outbox`), inbox z deduplikacją (`UniqueConstraint`).
- Brak dynamicznego SQL / niebezpiecznej deserializacji / blokującego HTTP w async (wszystkie wywołania async `httpx`).
- Brak N+1 w gorących ścieżkach; listy paginowane (poza wyjątkami w sekcji MEDIUM).
- Skille / tooling: `ruff check` i `import-linter` przechodzą; architektura testowana 170 plikami testów.

---

# BLOCKER

### [BLOCKER] (shell/user_service/framework/user/api/app.py:36; framework/user/user/api/router.py:41-46) — publiczna enumeracja kont `GET /api/v1/users/by-email`
- **Reguła:** review-security — ekspozycja danych; IDOR/enumeracja.
- **Dlaczego:** ścieżka w `USER_PUBLIC_EXACT`; endpoint bez autoryzacji zwraca `user_id` dla podanego e-maila (lub wyraźny 404, gdy nie istnieje) → wyrocznia istnienia konta i ujawnienie identyfikatora bez uwierzytelnienia. To odrębny problem — zostaje nawet jeśli docelowy schemat logowania (np. przez e-mail) tymczasowo zmieni postać.
- **Poprawka:** wyłączyć z publicznych, wymagać principala SERVICE/system, a odpowiedź ujednolicić tak, by nie ujawniała statusu rejestracji.

---

# CRITICAL

### [CRITICAL] (shell/tests/architecture/test_enterprise_patterns__test_no_service_locator_in_production.py:19,195) + analogiczne: test_domain_services_do_not_import_infrastructure.py, test_composition_root_in_bootstrap.py, test_framework_does_not_import_infrastructure.py, test_application_and_process_do_not_import_orm_models.py, test_domain_layer_imports.py — strażniki architektury są **próżne** (skanują nieistniejące katalogi)
- **Reguła:** review-dependency-architecture / arch-testing; architectural-discipline (zero wyjątków).
- **Dlaczego:** `BASE = pathlib.Path(__file__).parent.parent.parent.parent` rozwiązuje się do **repo root**, a pętle iterują `BASE/"domain"`, `BASE/"application"`, `BASE/"process"`, `BASE/"framework"` — takich katalogów w repo nie ma (kod jest w `shell/<bc>/<warstwa>`). `test_no_service_locator_in_production` skanuje więc zero plików i przechodzi na dowolnym kodzie. `test_domain_layer_imports.py` dodatkowo używa legacy prefiksów `shell.application/shell.infrastructure/shell.process` (nieistniejących przy formie per-BC). Testy nie wykryją przyszłego `container.resolve()` w handlerze ani cross-BC importu.
- **Poprawka:** przepisać na `_arch_helpers.iter_layer_files("domain"/"application"/"framework")` (helper rozwiązuje BASE poprawnie do `shell/`); w testach BC-isolation asować detektor `_cross_bc_violations()`, który jest napisany poprawnie, ale nigdy nie asertowany; usunąć legacy prefiksy.

### [CRITICAL] (shell/execution_service/bootstrap/execution/container/execution_core_container.py:552-633; framework/execution/node_execution/api/controller.py:90-95) — `DeleteNodeExecutionCommand` nie ma factory ani rejestracji → każde `DELETE /node-executions/{id}` kończy się 500 (KeyError)
- **Reguła:** review-application-layer — spójność rejestracji handlerów.
- **Dlaczego:** kontener rejestruje `CreateNodeExecutionCommand` (linia 628), ale nie `DeleteNodeExecutionCommand`; `handler-registration-integrity` wymaga factory+register dla każdego `.dispatch()`. `CommandBus.dispatch` robi `self._handler_factories[type(command)]` → KeyError. Endpoint istnieje w API, ale jest w 100% zepsuty.
- **Poprawka:** dodać `delete_node_execution_handler_factory = providers.Factory(DeleteNodeExecutionHandler, ...)` oraz `(DeleteNodeExecutionCommand, container.delete_node_execution_handler_factory)` do krotki registracji.

### [CRITICAL] (shell/user_service/infrastructure/user/user/persistence/sql/models/user.py:13-21; user_service/.../auth_session/models/auth_session.py:13-18; project_service/.../models/project.py, project_state.py:25, project_skill.py:24; ingestion_service/.../models/ingestion.py:25) — brak optymistycznego blokowania (kolumny wersji) na kluczowych agregatach → last-write-wins
- **Reguła:** review-concurrency-and-consistency — optymistyczne blokowanie.
- **Dlaczego:** tylko execution/session/scheduling/definition dziedziczą `VersionedMixin`; `User`, `AuthSession`, `Project`, `ProjectState`, `ProjectSkill`, `Ingestion` mają tylko `changed_at` (ustawiane przez aplikację). Dwa równoległe `change_user`/`change_project`/`change_ingestion` oba commitują — drugi cicho nadpisuje pierwszy. UoW mapuje `StaleDataError`→`ConcurrentModificationError`, ale na tych tabelach nigdy nie wystąpi.
- **Poprawka:** dodać `VersionedMixin` + `__mapper_args__ = {"version_id_col": cls.version}` do wszystkich mutowalnych agregatów (i migracji); konflikt mapować na 409.

### [CRITICAL] (shell/definition_service/infrastructure/definition/runner_config/persistence/sql/models/runner_config.py:22) — martwa kolumna `version` bez `version_id_col`
- **Reguła:** review-concurrency-and-consistency — blokowanie musi być aktywne albo nieobecne, nie iluzoryczne.
- **Dlaczego:** model ma `version: int` (default 1), ale brak `__mapper_args__` → SQLAlchemy nie wykonuje żadnego checku wersji. Kod *wygląda* na chroniony, a w praktyce nadpisania przechodzą cicho (false sense of safety).
- **Poprawka:** podpiąć `@declared_attr __mapper_args__` z `version_id_col` albo usunąć kolumnę do czasu implementacji.

### [CRITICAL] (shell/execution_service/domain/execution/aggregates/graph_execution/graph_execution.py:77-81, create_main_round/create_sub_graph 183-214) — agregat fabrykuje losowy `graph_definition_id`
- **Reguła:** review-domain-layer (rekonstrukcja/factory); no-empty-fallbacks (kardynalna).
- **Dlaczego:** przy braku `graph_definition_id` agregat generuje `GraphDefinitionIdRef.generate()` zamiast rzucić błąd — także w `restore()`. Powstaje GraphExecution bez wiązania do definicji, z nieistniejącym ID; zerwana integralność referencyjna z BC definition.
- **Poprawka:** wymusić wymagany `graph_definition_id` w `__init__`/`restore`; decyzję o braku wartości podejmuje handler (guard), nie agregat.

### [CRITICAL] (shell/session_service/domain/session/aggregates/session/session.py:95-106; shell/user_service/domain/user/aggregates/user/user.py:164-172; workflow.py:116-160, task_execution.py:115-138, node_execution.py:101-124) — metody FSM nie sprawdzają `_deleted_at`: soft-deleted agregat nie jest zamrożony
- **Reguła:** review-domain-layer — invariant nie do złamania przez legalną sekwencję metod.
- **Dlaczego:** `Session.delete()` a następnie `Session.close()` ustawia CLOSED na usuniętym agregacie; `User.enable()` po `delete()` przywraca usuniętego użytkownika do ACTIVE; analogicznie `Workflow.finish/fail/...`, `TaskExecution.*`, `NodeExecution.*` — guardy sprawdzają wyłącznie status. Kontrakt "usunięty = zamrożony" jest łamany niespójnie (Project/AuthSession już guardują na deleted).
- **Poprawka:** każda metoda mutująca zaczyna się od `if self._deleted_at.value is not None: raise ...`.

### [CRITICAL] (shell/ingestion_service/infrastructure/ingestion/persistence/sql/repositories/sql_ingestion_repository.py:36-43 + change/delete_ingestion_handler.py) — merge w SQL gubi `changed_at`/`deleted_at` → soft delete nigdy nie jest zapisany w bazie
- **Reguła:** review-persistence-and-migrations — mapper round-trip (konwersja gubi pole); utrata danych.
- **Dlaczego:** ścieżka merge aktualizuje tylko `ingestion_data`/`ingestion_context`; handlerzy polegają na soft-delete + save (`delete_ingestion_handler`). `DELETE /ingestions/{id}` nigdy nie ustawia `deleted_at` w SQL — byt po kolejnym odczycie pojawia się jako aktywny. InMemory zachowuje zmianę → asymetria i cicha utrata danych w produkcji.
- **Poprawka:** w gałęzi merge aktualizować wszystkie pola mutowalne (`changed_at`, `deleted_at`) jak w `user_change_model.py`; dodać test round-trip.

### [CRITICAL] (shell/user_service/migrations/versions/0001_user_baseline.py:53,73-74,95; models/user_state.py:23; platform/.../models/event_delivery.py:33,37,63,66,69; session_service/migrations/versions/0001_session_baseline.py:33,57,74 vs session_state.py:23) — rozjazd typów ORM↔migracja: `JSON` vs `JSONB`, `DateTime` naïve vs `timestamptz`
- **Reguła:** review-persistence-and-migrations — model-migration-sync.
- **Dlaczego:** ręczne migracje `user_service`/`session_service` definiują `sa.JSON()` i naïve `sa.DateTime()`, modele deklarują `JSONB` / `DateTime(timezone=True)`. Na PostgreSQL: operatory JSONB (`?`, `@>`) na kolumnie JSON padają; `inbox_claim_service` porównuje świadomy czasu `now` z kolumnami naïve — przy nie-UTC timezone strefa serwera przesuwa okna claim/reclaim.
- **Poprawka:** wygenerować migracje baseline z metadata ORM (wzorzec `create_service_tables` stosowany w ingestion/execution/definition/project/scheduling) albo ujednolicić kolumny na `sa.JSONB()` / `DateTime(timezone=True)`.

### [CRITICAL] (shell/execution_service/framework/execution/task_execution/api/router.py:28-35) — szeroki `except Exception` zamienia każdy błąd DI na HTTP 501 „not implemented"
- **Reguła:** review-error-handling / review-dependency-injection.
- **Dlaczego:** każda awaria kontenera/budowy query_bus jest maskowana jako „nie zaimplementowano" z `from None` (utrata tracebacku); to fałszywy kontrakt dostępności. Jeden z 16 site'ów `except Exception` — ten jest na ścieżce żądania.
- **Poprawka:** użyć `Depends(get_query_bus)` z platform; błędy niech propagują do handlera błędów; konkretny wyjątek logować z tracebackiem.

---

# HIGH

### [HIGH] (pyproject.toml:51-57) — `select = ["E", ...]` i `ignore = ["E501"]`: reguła jednocześnie wybrana i wyciszona
- **Reguła:** architectural-discipline (reguła jednocześnie w select i ignore).
- **Dlaczego:** prefiks `E` obejmuje `E501`; wymuszenie E501 raportuje 2545 naruszeń (linie >100 znaków istnieją). Deklarowany limit 100 znaków to fikcja; konfiguracja jest wewnętrznie sprzeczna.
- **Poprawka:** usunąć `E501` z `ignore` i naprawić linie (lub zdefiniować `[tool.ruff.lint.pycodestyle] max-line-length`) — bądź usunąć `E` z `select`.

### [HIGH] (run_tests.ps1:164) — próg pokrycia `--cov-fail-under=80` **nie może nigdy zawieść**
- **Reguła:** review-testing-and-ci; architectural-discipline (nigdy nie wycinaj się z bramki).
- **Dlaczego:** uruchomienie z `-AllowFailure`; skrypt przy błędzie i tak wypisze „OK:" i `exit 0`. Pokrycie nie jest egzekwowane też w GitHub Actions (brak `--cov` w żadnym workflow). Spadek pokrycia poniżej 80% shipuje się zielony.
- **Poprawka:** usunąć `-AllowFailure`; dodać krok `pytest --cov=shell --cov-fail-under=80` do `ci.yml`.

### [HIGH] (run_tests.ps1:158,139-155) — Bandit z `-AllowFailure`, pip-audit „nie jest release-blocking"
- **Reguła:** architectural-discipline / review-testing-and-ci.
- **Dlaczego:** lokalny runner zgłasza „All requested checks completed" mimo znalezisk Bandit -ll i mimo timeoutu audytu zależności. (Częściowa łagodność: `security-scan.yml:25-27` bramkuje `pip-audit --strict` i bandit w GitHub Actions — ale `run_tests.ps1` jest dokumentowanym "single source of truth".)
- **Poprawka:** zdjąć `-AllowFailure` z bandit; porażka/timeout pip-audit ma być twardym błędem.

### [HIGH] (pyproject.toml:109-120) — mypy strict wyłączony dla `shell.platform.bootstrap.*` i `shell.platform.framework.*`
- **Reguła:** review-python-code-quality — zero ucieczek ze strict typing.
- **Dlaczego:** composition roots, routery i middleware — dokładnie warstwy, gdzie słabe typowanie chowa błędy DI/kontraktów — są wyłączone z `disallow_untyped_defs` itd.; `ignore_missing_imports` dodatkowo osłabia motor/asyncpg/dependency_injector. Testy (`shell.tests.*`) są obroną uzasadnioną, bootstrap/framework nie.
- **Poprawka:** usunąć overrides dla bootstrap/framework (zostawić wąski tombstone dla testów) i oznaczyć kod.

### [HIGH] (.github/workflows/ci.yml:18-27, pozostałe 5 workflow) — mypy nie jest uruchamiany w CI
- **Reguła:** review-testing-and-ci.
- **Dlaczego:** żaden z 6 workflow nie wywołuje mypy; jedyna ochrona to wąski `test_mypy_domain_and_application_zero_errors.py` oraz lokalny `run_tests.ps1`. Ściśle typowanie dla framework/bootstrap i whole-shell nie jest sprawdzane na push/PR.
- **Poprawka:** `uv run mypy --no-incremental shell` w kroku unit-and-lint.

### [HIGH] (shell/execution_service/application/execution/node_execution/command_handlers/create_node_execution_handler.py:33-34,41-42) — `# type: ignore[attr-defined]` ukrywa **nieistniejące typy** `Identity`/`Time`
- **Reguła:** review-python-code-quality / review-application-layer.
- **Dlaczego:** porty to `IdGenerator` i `Clock`; `Identity` i `Time` nie istnieją nigdzie; ignor mypy ma przejść mimo błędnego importu. Handler dodatkowo przechowuje `self._identity`, ale generuje ID przez `NodeExecutionId.generate()` — port `identity` jest martwy.
- **Poprawka:** zaimportować/oznaczyć `IdGenerator`/`Clock`, usunąć `# type: ignore`, użyć `self._identity.new_id(NodeExecutionId)` (albo usunąć zależność).

### [HIGH] (shell/session_service/domain/session/aggregates/session_state/session_state.py:84-88; project_state.py:97; user_state.py:95; workflow_state.py:89; graph_execution_state.py:99; node_execution_state.py:87) — `change_state()` datuje zmiany na moment **utworzenia** agregatu
- **Reguła:** review-domain-layer — invarianty/timestamps; encja nie fałszuje czasu.
- **Dlaczego:** `_change(now=OccurredAt.from_datetime(self._created_at.value))` — sygnatura nie przyjmuje `now`, więc `changed_at` i `occurred_at` eventu `XxxStateChangedEvent` zawsze równają się `created_at`. Sfałszowana oś czasu w 6 agregatach `*_state`; retencja/outbox dostają serię identycznych znaczników.
- **Poprawka:** dodać `now: OccurredAt` do sygnatury `change_state` i przekazywać realny czas od callera.

### [HIGH] (shell/execution_service/domain/execution/aggregates/node_execution/node_execution.py:106-114; task_execution/task_execution.py:120-123) — `complete(result=...)`/`fail(error=...)` przyjmują dane i cicho je **gubią**
- **Reguła:** review-domain-layer — metody domenowe nie gubią danych wejściowych.
- **Dlaczego:** `NodeExecution.complete(result)` i `.fail(error)` nie zapisują wyniku/opisu błędu; `TaskExecution.complete(output: str = "")` ignoruje `output` (i propaguje pusty-string fallback). API obiecuje składowanie wyniku, które nie istnieje.
- **Poprawka:** składować wynik w encji/VO (`ExecutionResult`) lub usunąć parametr z sygnatury; usunąć fallback `""`.

### [HIGH] (shell/session_service/domain/session/aggregates/session/session.py:96,104,109; project.py:170,178; user.py:150,156) — ogólny `DomainError` zamiast dedykowanych wyjątków domenowych
- **Reguła:** review-domain-layer — dedykowane wyjątki.
- **Dlaczego:** guardy rzucają wspólny `DomainError`; katalogi wyjątków session/project/user są puste, a kontrast z `InvalidTaskStateError`/`InvalidNodeStateError` w execution. Konsumenci nie odróżnią „already deleted" od „invalid state".
- **Poprawka:** podklasy per agregat (np. `SessionDomainError`) rzucane w guardach; mapowanie na HTTP po typie.

### [HIGH] (shell/scheduling_service/domain/scheduling/aggregates/scheduler_definition/value_objects/scheduler_description.py:16-17; platform/domain/events/domain_event.py:19) — puste VO jako fallback (`SchedulerDescription.empty()` → `""`; `aggregate_name` default_factory `AggregateName("")`)
- **Reguła:** no-empty-fallbacks (kardynalna).
- **Dlaczego:** dokładnie wzorzec `VO("")` ze skilla: pozornie poprawna, martwa wartość; `AggregateName("")` powinno rzucić błąd walidacji.
- **Poprawka:** reprezentować brak opisu przez `None` (`SchedulerDescription | None`); wymagać `aggregate_name` lub walidować w `__post_init__`.

### [HIGH] (shell/execution_service/domain/execution/aggregates/graph_execution/graph_execution.py:157-161) — `change_status()` bez maszyny stanów: dowolne przejście statusu
- **Reguła:** review-domain-layer — tylko legalne przejścia stanów.
- **Dlaczego:** metoda ustawia dowolny `GraphExecutionStatus` na dowolnym statusie (PENDING→COMPLETED, SUSPENDED→VERIFYING) bez guardu poprzedniego stanu; invariant przechodzenia w martwą literę.
- **Poprawka:** modelować przejścia jako metody (`verify()`, `complete()`) z guardem, analogicznie do `Workflow`.

### [HIGH] (shell/scheduling_service/domain/scheduling/services/scheduler_orchestrator.py:61; dto/scheduler_definition.py:23; create_scheduler_definition_handler.py:70) — `action_type` jako surowy string + magic literal `"spawn_graph"` + fallback `""`
- **Reguła:** review-python-code-quality — stan jako StrEnum; no-empty-fallbacks.
- **Dlaczego:** literówka w stringu cicho kieruje każdą egzekucję w „unsupported action_type"; `""` maskuje brak pola konfiguracji zamiast błędu.
- **Poprawka:** `class ActionType(ValueObject, StrEnum)` z `SPAWN_GRAPH`; typować VO; wymagać wartości jawnie.

### [HIGH] (platform/infrastructure/messaging/transport/rabbit/rabbit_inbox_consumer.py:121-129,92-96) — szeroki `except Exception` → trwałe `reject(requeue=False)` przy błędzie transakcyjnym = utrata delivery
- **Reguła:** review-event-driven-integration / idempotencja-retry.
- **Dlaczego:** każdy niespójny błąd (DB w dół, reset połączenia) odrzuca wiadomość na stałe bez requeue/DLQ; przeżywa tylko, jeśli producent retry z outbox. Komendy wchodzące brokerem bezpośrednio giną.
- **Poprawka:** `reject(requeue=True)` (lub DLQ) dla błędów przejściowych; `reject(requeue=False)` tylko dla rozpoznanie nieprzetwarzalnych payloadów.

### [HIGH] (shell/user_service/framework/user/auth_session/api/router.py:53-60) — ciasteczko sesji `secure=False`
- **Reguła:** review-security — sekrety w transporcie.
- **Dlaczego:** token sesji (pełna kredencja) nadawany przez cookie bez flagi `Secure`; przy nieszyfrowanym HTTP / granicy HTTP→HTTPS może zostać podsłuchany i powtórzony.
- **Poprawka:** `secure=True` (sterowane flagą TLS deploymentu) + rozważyć prefiks `__Host-` i `SameSite=Strict`.

### [HIGH] (shell/execution_service/framework/execution/node_execution/api/controller.py:47-58 + bootstrap/.../execution_core_container.py:511-513) — `GetNodeExecutionByIdHandler` podpięty pod **result** query service → DTO bez `node_type` → 500
- **Reguła:** review-application-layer — pojedynczy read model; kontrakt query-side.
- **Dlaczego:** factory wstrzykuje `node_result_query_service` zwracające `NodeExecutionResultDto` (bez `node_type`), a controller woła `result.node_type` → AttributeError → 500 na `GET /node-executions/{id}`.
- **Poprawka:** wydzielić `NodeExecutionQueryService`/DTO i podpiąć get-by-id do niego.

### [HIGH] (login_auth_session_handler.py:68,85) — logika biznesowa w handlerze: polityka TTL i warunek ACTIVE
- **Reguła:** review-application-layer — handler koordynuje, nie decyduje.
- **Dlaczego:** `ExpiresAt.from_datetime(now.value + self._session_ttl)` (polityka długości sesji) i odrzucenie nie-ACTIVE to decyzje domenowe wykonane w warstwie aplikacji; agregat nie włada polityką lifetime.
- **Poprawka:** przenieść TTL→expiry do `AuthSession.create`/domain service; warunek ACTIVE do reguły domenowej.

### [HIGH] (change_project_handler.py:42-45; create/change_edge_execution_handler.py:49-53) — fallback `command.field if ... else wartość` = decyzja polityki merge w handlerze
- **Reguła:** no-empty-fallbacks / review-application-layer.
- **Dlaczego:** „keep existing on empty input" w aplikacji skleja „pole nie podane" z „pole puste" i dubluje politykę merge, która należy do agregatu; pusta wartość nie może zostać świadomie wyczyszczona.
- **Poprawka:** agregat przyjmuje opcjonalne pola (`name: ProjectName | None`) i sam decyduje o zachowaniu stanu przy `None`; pusty-problem walidowany na granicy API.

---

# MEDIUM

### [MEDIUM] (120 z 123 wystąpień `# noqa: TC00x`) — dyrektywy noqa wskazują **nieistniejące kody** (`TC001/TC002/TC003` zamiast `TCH001/...`)
- **Reguła:** noqa-enterprise-policy / architectural-discipline.
- **Dlaczego:** `ruff check --select RUF100` raportuje 120 „Unused noqa directive (non-enabled: TC001…)"; kod `TCH` = nowa nazwa `TC`; strażnik `test_noqa_has_justification` sprawdza tylko format, więc błędy przechodzą. ~97% supresji jest martwych i nie wycisza zamierzonej reguły TCH.
- **Poprawka:** poprawić kody na `TCH001/TCH002/TCH003` (albo usunąć, gdy reguła nie odpala) i dodać `RUF100` do `select`.

### [MEDIUM] (95 wystąpień) — produkcyjne `# type: ignore` bez uzasadnienia
- **Reguła:** review-python-code-quality.
- **Dlaczego:** np. `shell/platform/domain/ports/repository_port.py:14` (`# type: ignore[misc]` na generycznym Protocol — jedyne w warstwie domeny), `definition_service/.../memory/unit_of_work.py:132`, `reflective_integration_mapper.py:25-31`. Każdy ignor to ślepa plamka typów; klastry wokół `RepositoryPort`/event-mapping wskazują na słabe typowanie wspólnych protokołów.
- **Poprawka:** naprawić protokoły (kowaariancja, typowane mapowanie eventów); minimalnie dodać uzasadnienie w komentarzu przy każdym ignorze.

### [MEDIUM] (shell/scheduling_service/domain/scheduling/aggregates/scheduler_job/repositories/scheduler_job_repository.py:24-26 vs in_memory_scheduler_job_repository.py:12-13) — asymetria kontraktu repo: InMemory nie implementuje `list_all`/`list_enabled`
- **Reguła:** review-persistence-and-migrations — repository-contract-symmetry.
- **Dlaczego:** port deklaruje obie metody, SQL je ma, InMemory nie — konsument portu w profilu in-memory psuje się w runtime; testy dryfują od produkcji.
- **Poprawka:** zaimplementować obie metody w InMemory albo zawęzić port.

### [MEDIUM] (sql_edge_link_execution_repository.py:60-62; sql_user_repository.py:51-54 vs platform/.../in_memory_repository.py:49-58) — semantyka `exists()` różna dla soft-deleted: SQL=True, InMemory=False
- **Reguła:** review-persistence-and-migrations — repository-contract-symmetry.
- **Dlaczego:** po `delete()` SQL twierdzi że byt istnieje, InMemory że nie; guardy unikalności/idempotencji bazujące na `exists` zachowują się inaczej w teście i produkcji.
- **Poprawka:** ujednolicić (zalecane: SQL `exists` z `deleted_at IS NULL`).

### [MEDIUM] (shell/user_service/framework/user/user/api/app.py:71 vs platform/framework/api/setup.py:61-66,91-114) — niejednolity schemat błędów; `ProblemDetail`/`setup_api_common` to martwy kod
- **Reguła:** review-api-contracts — spójny format odpowiedzi.
- **Dlaczego:** żadna fabryka aplikacji nie woła `_register_error_handlers`/`setup_api_common`; rejestrowany jest tylko `DomainError` → `{"detail": ...}`, a HTTPException/validation/unhandled wracają domyślnymi kształtami FastAPI bez correlation id.
- **Poprawka:** użyć `setup_api_common(...)` w każdej fabryce albo zarejestrować brakujące handlery i ustandaryzować błędy do `ProblemDetail`.

### [MEDIUM] (platform/framework/api/setup.py:97-103) — CORS `allow_origins=["*"]` + `allow_credentials=True` (obecnie martwy kod w `setup_api_common`, gotowy do podpięcia)
- **Reguła:** review-security.
- **Dlaczego:** przy cookie-auth i niebezpiecznej kombinacji wildecard+credentials; dziś nieaktywne bo `setup_api_common` nie jest wołane, ale wystarczy je podpiąć (patrz powyżej), by ryzyko CSRF/cross-origin stało się realne.
- **Poprawka:** przy włączeniu `setup_api_common` ustawić jawną allowlistę originów i spójny `allow_credentials`.

### [MEDIUM] (definition_service/framework/definition/api/app.py:37-43; scheduling_service/framework/scheduling/api/app.py:32-38) — middleware auth montowany tylko gdy `api_key` — fail-open przy błęddzie konfiguracji
- **Reguła:** review-security — fail-closed.
- **Dlaczego:** `create_*_app(api_key="")` cicho uruchamia serwis bez żadnego auth; każdy endpoint staje się publiczny. Testy architektury pilnują obecnych miejsc wywołań, ale przyszła ścieżka startowa może je ominąć.
- **Poprawka:** zawsze montować `AuthMiddleware`; pusty klucz = jawny błąd konfiguracji.

### [MEDIUM] (platform/framework/api/middleware/audit_log.py:36-47) — logi audytowe zapisują surowy `query_string` (PII)
- **Reguła:** review-error-handling-and-logging — brak PII w logach.
- **Dlaczego:** `GET /api/v1/users/by-email?email=...` wpisuje adresy e-mail/PII do logu każdego żądania; `api_key` w query string też trafiłby do logów.
- **Poprawka:** logować ścieżkę/szablon route zamiast surowego query; redagować parametry.

### [MEDIUM] (platform/infrastructure/messaging/polling_worker.py:83) — heartbeat cicho połykany `with suppress(Exception)`
- **Reguła:** review-error-handling — cichy błąd to błąd niemonitorowany.
- **Dlaczego:** przy awarii zapisu heartbeatu worker dalej claimuje/procesuje inbox, a liveness degraduje się bez logu i metryki.
- **Poprawka:** `try/except` + `logger.exception` + metryka zdrowia.

### [MEDIUM] (platform/framework/api/middleware/api_key.py:105) — porównanie API key zwykłym `==`; ścieżka JWT bearer martwa (żaden `main.py` nie przekazuje `jwt_secret`)
- **Reguła:** review-security.
- **Dlaczego:** `==` teoretycznie podatne na timing dla wspólnego sekretu; cały `_validate_jwt` jest dziś nieosiągalny (dead auth code gotowy do nadużycia przy przyszłym podpięciu secretu).
- **Poprawka:** `secrets.compare_digest`; JWT albo podpiąć i przetestować, albo usunąć.

### [MEDIUM] (platform/framework/api/middleware/api_version.py / setup.py:111,125-135) — infrastruktura wersjonowania API martwa; wszystkie routy hardkodują `/api/v1`
- **Reguła:** review-api-contracts — wersjonowanie/backward compatibility.
- **Dlaczego:** `ApiVersionMiddleware`/`API_VERSION_REGISTRY` nieużywane; zmiana kontraktu nie może być wersjonowana — starzy konsumenci łamią się bez ścieżki migracji.
- **Poprawka:** podpiąć istniejący middleware + discovery router w fabrykach i wymagać bumpów wersji przy breaking zmianach DTO.

### [MEDIUM] (scheduling_service/.../scheduler_job/api/router.py:31-35; scheduler_execution/api/router.py:31-35; sql/.../query_service.py:47-53) — listy bez paginacji: zwracają całą tabelę
- **Reguła:** review-api-contracts — paginacja na listach.
- **Dlaczego:** pozostałe listy (users/sessions/projects/workflows) używają `Page[...]`; scheduling zwraca nieskończone tablice i nie skaluje się.
- **Poprawka:** `Page[SchedulerJobResponse]` z `page`/`page_size` + count.

### [MEDIUM] (task_execution_query_service.py:52-80; project_query_service.py:35-52; user_query_service.py:44-63) — paginacja OFFSET + osobne `COUNT(*)` na każdej liście
- **Reguła:** review-performance — keyset/cursor.
- **Dlaczego:** koszt O(depth) z głębokością offsetu + podwójne zapytanie per żądanie na gorących read ścieżkach.
- **Poprawka:** keyset na `(created_at, id)`; count cache'ować lub zaniechać.

### [MEDIUM] (platform/framework/api/ws/session_ws.py:14-34) — współdzielone `_connections` bez synchronizacji; socket usuwany przy każdym błędzie bez logu
- **Reguła:** review-concurrency-and-consistency — współdzielony mutable stan w runtime.
- **Dlaczego:** równoległe connect/disconnect/broadcast bez locka; cicha utrata gniazd przy fail send_json.
- **Poprawka:** `asyncio.Lock` wokół mutacji; logować błędy socketów.

### [MEDIUM] (execution_service/.../get_session_history_handler.py:19; get_session_by_id_handler.py:19) — `GetSessionHistory` to byte-for-byte duplikat `GetSessionById` (brak read modelu historii)
- **Reguła:** review-application-layer — separacja read modeli (CQRS).
- **Dlaczego:** oba delegują do `get_by_id` i zwracają `SessionDto`; zapytanie „historia" nie modeluje historii — konsument dostaje aktualny rekord.
- **Poprawka:** prawdziwy read model/snapshot + `SessionHistoryDto` z listą turnów/wiadomości.

### [MEDIUM] (user_service/.../dto/user_dto.py:13 vs user_query_service.py:31,71) — `UserDto.changed_at` nietypowany jako nullable przy nullable kolumnie źródłowej
- **Reguła:** review-application-layer — typy DTO odzwierciedlają read model.
- **Dlaczego:** `changed_at: datetime` bez `| None` wypełniany z `Mapped[datetime | None]` → utajone `None`-do-datetime w kontrakcie.
- **Poprawka:** `datetime | None` (jak w DTO Session/Project).

### [MEDIUM] (session/mappers/session_entity_to_model.py:24; session_change_model.py:13,18) — mappery sięgają do prywatnego stanu agregatu
- **Reguła:** review-application-layer — enkapsulacja.
- **Dlaczego:** `session._status`, `session._deleted_at` zamiast publicznych właściwości (`session_status`, `deleted_at`); sprzęga mapper z implementacją i omija invarianty/typizowane accessory.
- **Poprawka:** używać publicznych właściwości.

### [MEDIUM] (dto session.py/user_dto.py/project.py/workflow.py:14-15) — DTO kontraktowe wyciekają pola audytowe (`changed_at`, `deleted_at`)
- **Reguła:** review-application-layer — DTO bez pól technicznych/ORM.
- **Dlaczego:** timestampy soft-delete/audit z write-modelu w kontrakcie API; spaja kontrakt z semantyką kolumn.
- **Poprawka:** usunąć pola audytowe z DTO kontraktowych albo eksponować tylko jawnie wymagane invarianty.

### [MEDIUM] (logout_auth_session_handler.py:25-35) — handler cicho połyka przypadki, które domena już obsługuje
- **Reguła:** review-application-layer — handler koordynuje, nie decyduje.
- **Dlaczego:** `if not command.token: return`, `if auth_session is None or is_deleted: return`, `if revoked_at: return` re-implementują semantykę `revoke()` (która rzuca błędy dedykowane); błędy cicho znikają.
- **Poprawka:** wywołać `auth_session.revoke(now)` i pozwolić agregatowi decydować; idempotentny 204 obsłużyć w API warstwie.

### [MEDIUM] (StateData: platform/domain/value_objects/state_data.py:12-14 + `StateData(JsonStr("{}"))` w mappery model_to_entity: session/workflow/project/user_state) — VO `StateData` bez walidacji JSON + fallback `"{}"`
- **Reguła:** review-domain-layer — VO walidacja w `__post_init__`; no-empty-fallbacks.
- **Dlaczego:** dowolny string (także nie-JSON) przechodzi; mappery budują `{}` jako fallback braku danych zamiast `None`.
- **Poprawka:** walidacja JSON w `__post_init__`; `None` gdy brak danych.

### [MEDIUM] (RepoUrl/ChangedAt/DeletedAt/RevokedAt `__str__` → `self.value or ""`) — `__str__` zwraca pusty string dla braku wartości
- **Reguła:** no-empty-fallbacks.
- **Dlaczego:** np. `shell/project_service/domain/project/aggregates/project/value_objects/repo_url.py:18` — serializacja/`__str__` zamienia brak na `""`; dokładnie wzorzec `RepoUrl("")` ze skilla.
- **Poprawka:** `None`/jawne `"<none>"` w kontrakcie serializacji, nigdy po cichu `""`.

---

# LOW

### [LOW] (shell/platform/domain/ports/repository_port.py:14) — jedyny `# type: ignore[misc]` w warstwie domeny, na centralnym kontrakcie repozytorium
- Reguła: review-python-code-quality; domena to liść — zero wyjątków.
- Poprawka: rozwiązać przez wariancję (`covariant`/`contravariant`) albo dokumentować ograniczenie mypy.

### [LOW] (shell/execution_service/domain/execution/aggregates/workflow/workflow.py:42; workflow_state.py:35; user/session/task_execution_state.py) — `AggregateRoot["WorkflowId"]` z literałem string zamiast typu
- Reguła: review-domain-layer — precyzja generyków domeny.
- Poprawka: usunąć cudzysłowy (importować `WorkflowId` do klasy).

### [LOW] (shell/ingestion_service/infrastructure/ingestion/persistence/sql/mappers/ingestion_model_to_entity.py:25-26) — lokalny `_utc` dubluje platformowy `ensure_utc`
- Reguła: review-python-code-quality — duplikacja (DRY); prywatny helper importowany cross-service.
- Poprawka: użyć `ensure_utc`; wypromować go na publiczny util platform.

### [LOW] (shell/execution_service/.../node_result_query_service.py:46-70 vs framework/node_execution/api/router.py:47-55) — `GET /node-executions/{id}/result` eksponuje wymagany `workflow_id`, który niczego nie filtruje
- Reguła: review-api-contracts — martwe/ukryte pola kontraktu.
- Poprawka: usunąć parametr albo faktycznie nim ograniczyć zapytanie.

### [LOW] (shell/execution_service/framework/execution/edge_execution/api/router.py:49-63) — `PUT /edge-executions/{id}` zwraca 200 z pustym body; konwencje slaszy niespójne (`POST ""` vs `POST "/"`)
- Reguła: review-api-contracts — poprawne kody HTTP.
- Poprawka: 204 dla update no-body; znormalizować trasy.

### [LOW] (shell/user_service/framework/user/user/api/router.py:41-46) — `GET /users/by-email` zwraca `LoginResponse` (model nazwany od capability logowania)
- Reguła: review-api-contracts — nazewnictwo kontraktu.
- Poprawka: dedykowany `UserByEmailResponse`.

### [LOW] (shell/scheduling_service/domain/.../scheduler_orchestrator.py:42,93) — `dict[str, Any] | None` w kontrakcie publicznej metody domenowej
- Reguła: review-python-code-quality — `Any` jako kontrakt.
- Poprawka: `StateData`/`TypedDict` zamiast `dict[str, Any]`.

### [LOW] (shell/session_service/domain/session/services/session_management_service.py:21) — `self._id_generator_` (literówka wzorca `_id_generator`)
- Reguła: review-python-code-quality — jakość domeny.
- Poprawka: `self._id_generator`.

---

# NIT

### [NIT] (workflow.py:116-123) — `Workflow.start_at(...)` to martwy stub: tylko guard, brak mutacji/eventu, `work_dir: str | None` (surowe str), parametry nieużywane
- Reguła: review-domain-layer — publiczne API domeny bez efektu.
- Poprawka: usunąć albo zaimplementować realną mutację ze `WorkDir` VO i eventem.

### [NIT] (domain aggregates: `# noqa: TC001` runtime import `JsonStr`, np. node_execution_state.py:24, project_state.py:21, scheduler_orchestrator.py:10) — powtarzany wzorzec; gdzie pole to tylko anotacja, import pod `TYPE_CHECKING`
- Poprawka: centralizować alias typu na platformie per BC.

---

## Suplement: testy/CI — ustalenia dodatkowe

### [HIGH] (tests-optimistic/test_repo_debug.py:37-81) — jedyny test optymistycznego blokowania **nigdy się nie uruchamia**
- **Reguła:** review-testing-and-ci — invariant współbieżności bez egzekwowalnego strażnika.
- **Dlaczego:** test `ConcurrentModificationError` leży w `tests-optimistic/` — poza `testpaths`, bez odwołania w żadnym workflow/script. Cały katalog ma pycache zbudowany pod **Python 3.14** (projekt celuje w 3.11; CI używa 3.12) i jest sierotą.
- **Poprawka:** przenieść jako prawidłowo nazwany test (np. `test_workflow_optimistic_locking.py`) do `shell/tests/execution_service/.../integration/sql_sqlite` (zestaw zawsze uruchamiany); usunąć katalog `tests-optimistic`.

### [MEDIUM] (shell/tests/session_service/unit/test_session_seed.py:10-17) — test z realną bazą SQLite w katalogu unit, na niekonsekwentnej głębokości (`session_service/unit` zamiast `session_service/session/unit`)
- **Reguła:** review-testing-and-ci — integracyjny test w lokalizacji unit.
- **Poprawka:** przenieść do `.../integration/sql_sqlite` (zestaw zawsze uruchamiany); otypować fixture.

---

## Rekomendowana kolejność napraw

1. **BLOCKER bezpieczeństwa** — zamknięcie publicznego endpointu enumeracji użytkowników (przeniesienie poza listę publiczną, wymóg principala, ujednolicona odpowiedź nieujawniająca statusu rejestracji).
2. **Próżne strażniki architektury** — przepisać na `_arch_helpers` (bez tego testy nie chronią niczego).
3. **Registracja `DeleteNodeExecutionCommand`** i naprawa phantom `Identity/Time`.
4. **Domena** — guard deleted we wszystkich FSM, usunięcie `graph_definition_id generate()`, realny `now` w `change_state`, domknięcie eventów FSM.
5. **Spójność danych** — soft-delete w `sql_ingestion_repository`, ujednolicenie `exists()`, wersjonowanie `User/Project/...`, regeneracja migracji.
6. **Bramki CI** — usunięcie `-AllowFailure` (coverage/bandit), dodanie mypy do CI, poprawa `# noqa` na `TCH*`, śledztwo E501.

---

*Raport wygenerowany na podstawie skilli `review-*`; każda pozycja oznaczona jest lokalizacją `file:line`, regułą i proponowaną poprawką. Ustalenia oznaczone BLOCKER/CRITICAL zweryfikowane bezpośrednio w źródłach.*