# Code Review — SHELL (raport ustaleń)

Data: 2026-08-30
Zakres: cały monorepo `shell/` — 8 bounded contextów (`platform` + 7 × `*_service`), ~2400 plików produkcyjnych, ~1300 testów.
Metodyka: przegląd wykonany wg zestawu skilli `review-*` (`.opencode/skills/review/`); narzędzia uruchomione lokalnie (`ruff`, `import-linter`, `mypy --no-incremental` — wszystkie zakończone bez błędów **w aktualnej konfiguracji**), plus 6 równoległych przeglądów domenowych z weryfikacją najpoważniejszych ustaleń w źródłach.

Klasyfikacja wg `review-severity-levels`: **BLOCKER / CRITICAL / HIGH / MEDIUM / LOW / NIT**.

---

## Podsumowanie wykonawcze

Kod jest **architektonicznie czysty w warstwach, które przeszły do nowego modelu per-BC**: zero bezpośrednich importów między BC, zero importów infrastruktury/ORM w warstwie domeny, porty i adaptery poprawnie rozdzielone, UoW + outbox w jednej transakcji, idempotencja inbox, segregacja read/write (CQRS). To bardzo dobra baza.

Najpoważniejsze problemy leżą **nie w modelu domeny, lecz w granicach bezpieczeństwa i w mechanizmach, które mają chronić architekturę przed regresją**:

1. **Bramki CI są częściowo dekoracyjne** — próg pokrycia `--cov-fail-under=80` i Bandit uruchamiane z `-AllowFailure` (reguła zero-wyjątków); mypy nie jest uruchamiany w GitHub Actions. (HIGH)
2. **Dziury w integracji** — `GetNodeExecutionByIdHandler` podpięty pod result-service (500), synchronizacja InMemory↔SQL asymetryczna.
3. **Domena** — `complete/fail` gubią wyniki, ogólne `DomainError`, maszyna stanów `change_status()`, puste VO.

> **Naprawione w trakcie review:** publiczna enumeracja `GET /users/by-email`; próżne strażniki architektury (+ meta-test `test_arch_guards_scan_real_code.py`); retention CLI z `framework/*/cli/` do `infrastructure/*/cli/`; rejestracja `DeleteNodeExecutionCommand`; phantom `Identity`/`Time`; szeroki `except`→501 w task_execution; cookie sesji `secure=True`+`SameSite=Strict`; `UserByEmailResponse`; optimistic locking (`VersionedMixin` + Integer `version` dla User/AuthSession/Project/Ingestion/runner_config/graph_definition_embedding); soft-delete w `sql_ingestion_repository`; regeneracja migracji user/session z ORM metadata; guard `_deleted_at` w FSM; realny `now` w `*_state.change_state()`; zakaz fabrykowania `graph_definition_id`; przeniesiony test optimistic locking do stale uruchamianego zestawu (usunięty katalog `tests-optimistic`). Dodatkowo (niskie koszty): `AggregateRoot[X]` bez literałów string; `UserDto.changed_at` nullable; heartbeat `polling_worker` logowany; `secrets.compare_digest` dla API key; `exists()` SQL uwzględnia soft-deleted (user/edge_link/ingestion); `SchedulerDescription` z walidacją + usunięty `empty()`; `logout` delegujący do `revoke()` (idempotentny 204); lock + log w `session_ws`; `ensure_utc` zamiast lokalnego `_utc` w ingestion; mappery session używają publicznych accessorów; `scheduler_orchestrator` przyjmuje `StateData` zamiast `dict[str, Any]`; `RepositoryPort` bez `# type: ignore` (TId contravariant); test `session_seed` przeniesiony do `integration/sql_sqlite`.

---

## Pozytywy (zweryfikowane, brak uwag)

- Kierunek zależności: `domain` nie importuje `infrastructure`/ORM; `application` zależy od portów (0 naruszeń w regex na wszystkich BC).
- Brak Service Locator / `container.resolve()` w kodzie biznesowym; DI per BC izolowane, UoW rejestrowany jako `providers.Factory` (nie singleton).
- Zdarzenia domenowe: frozen dataclass, nazwy w czasie przeszłym, emitowane w metodach domenowych.
- Transactional outbox poprawny (`SqlAlchemyUnitOfWorkBase._write_staged_outbox`), inbox z deduplikacją (`UniqueConstraint`).
- Brak dynamicznego SQL / niebezpiecznej deserializacji / blokującego HTTP w async (wszystkie wywołania async `httpx`).
- Brak N+1 w gorących ścieżkach; listy paginowane (poza wyjątkami w sekcji MEDIUM).
- Skille / tooling: `ruff check` i `import-linter` przechodzą; architektura testowana 181 plikami testów (w tym strażnikiem-strażników `test_arch_guards_scan_real_code.py`).

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

### [HIGH] (shell/execution_service/domain/execution/aggregates/node_execution/node_execution.py:106-114; task_execution/task_execution.py:120-123) — `complete(result=...)`/`fail(error=...)` przyjmują dane i cicho je **gubią**
- **Reguła:** review-domain-layer — metody domenowe nie gubią danych wejściowych.
- **Dlaczego:** `NodeExecution.complete(result)` i `.fail(error)` nie zapisują wyniku/opisu błędu; `TaskExecution.complete(output: str = "")` ignoruje `output` (i propaguje pusty-string fallback). API obiecuje składowanie wyniku, które nie istnieje.
- **Poprawka:** składować wynik w encji/VO (`ExecutionResult`) lub usunąć parametr z sygnatury; usunąć fallback `""`.

### [HIGH] (shell/session_service/domain/session/aggregates/session/session.py:96,104,109; project.py:170,178; user.py:150,156) — ogólny `DomainError` zamiast dedykowanych wyjątków domenowych
- **Reguła:** review-domain-layer — dedykowane wyjątki.
- **Dlaczego:** guardy rzucają wspólny `DomainError`; katalogi wyjątków session/project/user są puste, a kontrast z `InvalidTaskStateError`/`InvalidNodeStateError` w execution. Konsumenci nie odróżnią „already deleted" od „invalid state".
- **Poprawka:** podklasy per agregat (np. `SessionDomainError`) rzucane w guardach; mapowanie na HTTP po typie.

### [HIGH] (shell/platform/domain/events/domain_event.py:19) — `DomainEvent.aggregate_name` default_factory tworzy `AggregateName("")` — puste VO jako fallback
- **Reguła:** no-empty-fallbacks (kardynalna).
- **Dlaczego:** wzorzec `VO("")` — pozornie poprawna, martwa wartość; event zbudowany poza agregatem (bez `append_event`) nosi pustą nazwę agregatu.
- **Poprawka:** wymusić jawny `aggregate_name` (bez default_factory do pustego VO) albo walidować niepustość w `AggregateName.__post_init__` i świadomie zmieniać wszystkich bezpośrednich konstruktorów eventów.

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

### [MEDIUM] (platform/framework/api/middleware/api_key.py) — ścieżka JWT bearer martwa (żaden `main.py` nie przekazuje `jwt_secret`)
- **Reguła:** review-security.
- **Dlaczego:** cały `_validate_jwt` jest nieosiągalny (dead auth code gotowy do nadużycia przy przyszłym podpięciu secretu).
- **Poprawka:** JWT albo podpiąć i przetestować, albo usunąć.

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

### [MEDIUM] (execution_service/.../get_session_history_handler.py:19; get_session_by_id_handler.py:19) — `GetSessionHistory` to byte-for-byte duplikat `GetSessionById` (brak read modelu historii)
- **Reguła:** review-application-layer — separacja read modeli (CQRS).
- **Dlaczego:** oba delegują do `get_by_id` i zwracają `SessionDto`; zapytanie „historia" nie modeluje historii — konsument dostaje aktualny rekord.
- **Poprawka:** prawdziwy read model/snapshot + `SessionHistoryDto` z listą turnów/wiadomości.

### [MEDIUM] (dto session.py/user_dto.py/project.py/workflow.py:14-15) — DTO kontraktowe wyciekają pola audytowe (`changed_at`, `deleted_at`)
- **Reguła:** review-application-layer — DTO bez pól technicznych/ORM.
- **Dlaczego:** timestampy soft-delete/audit z write-modelu w kontrakcie API; spaja kontrakt z semantyką kolumn.
- **Poprawka:** usunąć pola audytowe z DTO kontraktowych albo eksponować tylko jawnie wymagane invarianty.

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

### [LOW] (shell/execution_service/.../node_result_query_service.py:46-70 vs framework/node_execution/api/router.py:47-55) — `GET /node-executions/{id}/result` eksponuje wymagany `workflow_id`, który niczego nie filtruje
- Reguła: review-api-contracts — martwe/ukryte pola kontraktu.
- Poprawka: usunąć parametr albo faktycznie nim ograniczyć zapytanie.

### [LOW] (shell/execution_service/framework/execution/edge_execution/api/router.py:49-63) — `PUT /edge-executions/{id}` zwraca 200 z pustym body; konwencje slaszy niespójne (`POST ""` vs `POST "/"`)
- Reguła: review-api-contracts — poprawne kody HTTP.
- Poprawka: 204 dla update no-body; znormalizować trasy.

---

> **False positive skreślony:** `self._id_generator_` (session_management_service) to **świadoma konwencja** testów architektury — `test_domain_services_are_stateless` traktuje atrybuty z **końcowym podkreśleniem** jako wstrzyknięte zależności (stateless service). Zmiana na `_id_generator` złamała regułę; przywrócono oryginał.

---

# NIT

### [NIT] (workflow.py:116-123) — `Workflow.start_at(...)` to martwy stub: tylko guard, brak mutacji/eventu, `work_dir: str | None` (surowe str), parametry nieużywane
- Reguła: review-domain-layer — publiczne API domeny bez efektu.
- Poprawka: usunąć albo zaimplementować realną mutację ze `WorkDir` VO i eventem.

### [NIT] (domain aggregates: `# noqa: TC001` runtime import `JsonStr`, np. node_execution_state.py:24, project_state.py:21, scheduler_orchestrator.py:10) — powtarzany wzorzec; gdzie pole to tylko anotacja, import pod `TYPE_CHECKING`
- Poprawka: centralizować alias typu na platformie per BC.

---

## Suplement: testy/CI — ustalenia dodatkowe

### [MEDIUM] (shell/tests/session_service/session/integration/sql_sqlite/test_session_seed.py — poprawione) — test seed przeniesiony z `session_service/unit` do integration/sql_sqlite i otypowywany

---

## Rekomendowana kolejność napraw

1. **Bramki CI** — usunięcie `-AllowFailure` (coverage/bandit), dodanie mypy do CI, poprawa `# noqa` na `TCH*`, śledztwo E501.
2. **Obsługa błędów i bezpieczeństwo** — dedykowane wyjątki domenowe zamiast `DomainError`; rabbit inbox consumer `requeue=True`; `ProblemDetail` zamiast martwego kodu; fail-closed auth (definition/scheduling); redakcja PII w logach audytu.
3. **Integracja** — prawdziwy read model `GetNodeExecutionById`; asymetrie InMemory↔SQL (`exists()`, scheduler repo); `GetSessionHistory` jako prawdziwy read model.
4. **Domena (pozostałe)** — składowanie wyniku w `complete/fail`; maszyna stanów `change_status()`; dedykowane typy (`ActionType`, `StateData`), usunięcie pustych VO.
5. **API/struktura** — `ProblemDetail`, wersjonowanie API, paginacja scheduling/OFTSET, spójne kody HTTP, uporządkowanie `# noqa`/`# type: ignore`.

---

*Raport wygenerowany na podstawie skilli `review-*`; każda pozycja oznaczona jest lokalizacją `file:line`, regułą i proponowaną poprawką. Ustalenia oznaczone BLOCKER/CRITICAL zweryfikowane bezpośrednio w źródłach.*