# Code Review — SHELL (raport ustaleń)

Data: 2026-08-30
Zakres: cały monorepo `shell/` — 8 bounded contextów (`platform` + 7 × `*_service`), ~2400 plików produkcyjnych, ~1300 testów.
Metodyka: przegląd wykonany wg zestawu skilli `review-*` (`.opencode/skills/review/`); narzędzia uruchomione lokalnie (`ruff`, `import-linter`, `mypy --no-incremental` — wszystkie zakończone bez błędów **w aktualnej konfiguracji**), plus 6 równoległych przeglądów domenowych z weryfikacją najpoważniejszych ustaleń w źródłach.

Klasyfikacja wg `review-severity-levels`: **BLOCKER / CRITICAL / HIGH / MEDIUM / LOW / NIT**.

---

## Podsumowanie wykonawcze

Kod jest **architektonicznie czysty w warstwach, które przeszły do nowego modelu per-BC**: zero bezpośrednich importów między BC, zero importów infrastruktury/ORM w warstwie domeny, porty i adaptery poprawnie rozdzielone, UoW + outbox w jednej transakcji, idempotencja inbox, segregacja read/write (CQRS). To bardzo dobra baza.

Najpoważniejsze problemy leżą **nie w modelu domeny, lecz w granicach bezpieczeństwa i w mechanizmach, które mają chronić architekturę przed regresją**:

1. **Bramki CI/typy** — mypy strict wyłączony dla `bootstrap/framework`; ~100 produkcyjnych `# type: ignore` bez uzasadnienia. (HIGH/MEDIUM)
2. **Domena (pozostałe)** — DTO wyciekają pola audytowe (`changed_at`, `deleted_at`); `GetSessionHistory` jako duplikat read modelu.
3. **API/bezpieczeństwo** — `setup_api_common`/`ProblemDetail` martwe (niejednolity schemat błędów), JWT bearer i wersjonowanie API martwe, paginacja (scheduling bez limitów, OFFSET+COUNT), `StateData("{}")` fallback w mappery.

> **Naprawione w trakcie review:** publiczna enumeracja `GET /users/by-email`; próżne strażniki architektury (+ meta-test `test_arch_guards_scan_real_code.py`); retention CLI z `framework/*/cli/` do `infrastructure/*/cli/`; rejestracja `DeleteNodeExecutionCommand`; phantom `Identity`/`Time`; szeroki `except`→501 w task_execution; cookie sesji `secure=True`+`SameSite=Strict`; `UserByEmailResponse`; optimistic locking (`VersionedMixin` + Integer `version` dla User/AuthSession/Project/Ingestion/runner_config/graph_definition_embedding); soft-delete w `sql_ingestion_repository`; regeneracja migracji user/session z ORM metadata; guard `_deleted_at` w FSM; realny `now` w `*_state.change_state()`; zakaz fabrykowania `graph_definition_id`; przeniesiony test optimistic locking do stale uruchamianego zestawu (usunięty katalog `tests-optimistic`). Dodatkowo (niskie koszty): `AggregateRoot[X]` bez literałów string; `UserDto.changed_at` nullable; heartbeat `polling_worker` logowany; `secrets.compare_digest` dla API key; `exists()` SQL uwzględnia soft-deleted (user/edge_link/ingestion); `SchedulerDescription` z walidacją + usunięty `empty()`; `logout` delegujący do `revoke()` (idempotentny 204); lock + log w `session_ws`; `ensure_utc` zamiast lokalnego `_utc` w ingestion; mappery session używają publicznych accessorów; `scheduler_orchestrator` przyjmuje `StateData` zamiast `dict[str, Any]`; `RepositoryPort` bez `# type: ignore` (TId contravariant); test `session_seed` przeniesiony do `integration/sql_sqlite`.

> **Naprawione w rundzie 2:** fail-closed auth w `create_definition_app`/`create_scheduling_app` (zawsze `AuthMiddleware`, pusty `api_key` = `ValueError`); `ActionType(ValueObject, StrEnum)` zamiast magic `"spawn_graph"`; `Project.change()` z polityką merge (`ProjectName | None`/`RepoUrl | None`), merge usunięty z `change_project_handler`; TTL→`AuthSession.create(session_ttl=...)` + reguła ACTIVE jako domenowa `assert_user_can_login`; `InMemorySchedulerJobRepository.list_all/list_enabled` (symetria z portem); `GET /node-executions/{id}/result` wymusza `workflow_id`; `PUT /edge-executions/{id}` → 204; usunięty `query_string` (PII) z `AuditLogMiddleware`; usunięty martwy `Workflow.start_at` (+ testy architektury). Noqa: wpis o „martwych TC" **był fałszywym pozytywem** — `ruff --select RUF100` wyłącza regułę TC i błędnie nazywa aktywne supresje „nieużywanymi"; kody `TC001/TC003` są poprawne, supresje uzupełnione o uzasadnienia, a prawdziwe annotation-only importy (`Namespace`, `date`, `JsonStr`, `timedelta`) przeniesione do `TYPE_CHECKING`.

> **Naprawione w rundzie 3 (proste tematy):** CORS w `setup_api_common` — zamiast `allow_origins=["*"]`+`allow_credentials=True` jawny parametr `allowed_origins` (brak wildcard+credentials); martwe `__str__` w `RepoUrl`/`ChangedAt`/`DeletedAt`/`RevokedAt` **usunięte** (nic ich nie używa — cały dostęp do wartości idzie przez `.value`; fallback `""` zniknął razem z nimi).

> **Naprawione w rundzie 4:** pełne rozdzielenie eventów integracyjnych od komend — **zero `contract_type` w całym kodzie**. Usunięty wspólny `EnvelopeDeserializer`/`EventDeserializer` (facade); dwa niezależne deserializery: `IntegrationEventDeserializer` (`integration_event_name`) i `CommandDeserializer` (`command_name`). Rozbite nośniki transportu: `IntegrationEventDeliveryEnvelope` / `CommandDeliveryEnvelope` (baza `DeliveryEnvelopeBase`), `EnvelopeCodec` z polami `integration_event_name`/`command_name`; routing `event.<name>`/`command.<name>`. Comendy mają własny znacznik czasu **`dispatched_at`** (eventy — `occurred_at`): pole `CommandDeliveryEnvelope.dispatched_at`, kolumny `outbox_command`/`inbox_command.dispatched_at`, JSON `dispatched_at`, `CommandDeserializer.deserialize(..., dispatched_at, ...)`. Kontenery: event transport+relay i komendowy transport+relay rozdzielone. Wspólna tylko niska mechanika brokera (`_RabbitPublisher`). Kolumny DB przemianowane: `event_type`→`integration_event_name`, `command_type`→`command_name` (w outbox/inbox/audyt), procesory czytają `row.integration_event_name`/`row.command_name`, `_type_name`→`_message_name`. Dodatkowo usunięta serializacja eventów domenowych (`DomainEventSerializer`, `EventEnvelopeSerializer`, `EnvelopeSerializer`, `serialize_staged_events`, `SqlAuditPublisher`, `InMemoryOutboxStore`) — domenowe tylko mapujemy do integracyjnych (`ReflectiveIntegrationMapper`→`IntegrationEventSerializer`); testy inbox przebudowane na tę pętlę. Wcześniej z `DomainEvent` usunięte także `aggregate_name` i `schema_version` (event identyfikuje agregat przez typ; wersja kontraktu żyje w `IntegrationEvent`/wire).

> **Naprawione w rundzie 5 (pełne rozdzielenie + rdzeń modelu komend):** Komendy i eventy **nie dzielą już żadnych obiektów/spójnych plików/katalogów** — osobne poroty (`ports/transport/event_transport.py`, `command_transport.py`, envel·opy bez wspólnej bazy `DeliveryEnvelopeBase`), osobne paczki `messaging/event_transport/` i `messaging/command_transport/` (osobne codec, relay **bez wspólnego `_RelayBase`**, osobne adaptery Rabbit `RabbitEvent*`/`RabbitCommand*` i inboks-konsumenci). Komendy: **`issued_at`** (zamiast `occurred_at`/`dispatched_at`), `command_id`, `source_service`, `target_service`, `schema_version` — kolumny `outbox_command`/`inbox_command`, `CommandDeliveryEnvelope` i wire JSON. Wprowadzony rdzeń P1 dokumentu `command.md`: `CommandContract` + fail-fast `build_command_contract_registry`, port `AsyncCommandDispatcher`, `SqlCommandOutboxWriter` (append na aktywnej sesji **bez ukrytego commitu** — atomowość ze zmianą domeny), `StandaloneSqlCommandOutboxWriter` (osobna sesja + commit), `SqlAsyncCommandDispatcher` (kontrakt po klasie, walidacja `target_service`, aktywna sesja z `get_session_scope`).

---

## Pozytywy (zweryfikowane, brak uwag)

- Kierunek zależności: `domain` nie importuje `infrastructure`/ORM; `application` zależy od portów (0 naruszeń w regex na wszystkich BC).
- Brak Service Locator / `container.resolve()` w kodzie biznesowym; DI per BC izolowane, UoW rejestrowany jako `providers.Factory` (nie singleton).
- Zdarzenia domenowe: frozen dataclass, nazwy w czasie przeszłym, emitowane w metodach domenowych.
- Transactional outbox poprawny (`SqlAlchemyUnitOfWorkBase._write_staged_outbox`), inbox z deduplikacją (`UniqueConstraint`).
- Brak dynamicznego SQL / niebezpiecznej deserializacji / blokującego HTTP w async (wszystkie wywołania async `httpx`).
- Brak N+1 w gorących ścieżkach; listy paginowane (poza wyjątkami w sekcji MEDIUM).
- Skille / tooling: `ruff check` i `import-linter` przechodzą; architektura testowana 187 plikami testów (w tym strażnikiem-strażników `test_arch_guards_scan_real_code.py` + 6 nowych strażników regresji).

---

# HIGH

### [HIGH] (pyproject.toml:109-120) — mypy strict wyłączony dla `shell.platform.bootstrap.*` i `shell.platform.framework.*`
- **Reguła:** review-python-code-quality — zero ucieczek ze strict typing.
- **Dlaczego:** composition roots, routery i middleware — dokładnie warstwy, gdzie słabe typowanie chowa błędy DI/kontraktów — są wyłączone z `disallow_untyped_defs` itd.; `ignore_missing_imports` dodatkowo osłabia motor/asyncpg/dependency_injector. Testy (`shell.tests.*`) są obroną uzasadnioną, bootstrap/framework nie.
- **Poprawka:** usunąć overrides dla bootstrap/framework (zostawić wąski tombstone dla testów) i oznaczyć kod.

---

# MEDIUM

### [MEDIUM] (produkcyjne `# type: ignore` bez uzasadnienia)
- **Reguła:** review-python-code-quality.
- **Dlaczego:** ~100 wystąpień w kodzie produkcyjnym bez uzasadnienia w komentarzu, np. `definition_service/.../memory/unit_of_work.py:124,127,132`, `platform/infrastructure/mapping/reflective_integration_mapper.py:25-31`. Każdy ignor to ślepa plamka typów; klastry wokół generycznych protokołów wskazują na słabe typowanie wspólnych kontraktów. (Uwaga: jedyny case w domenie — `repository_port.py` — naprawiony przez wariancję `TId`; strażnik `test_domain_has_no_type_ignore` pilnuje, by nie wrócił.)
- **Poprawka:** naprawić protokoły (wariancja, typowane mapowanie eventów) albo dodać uzasadnienie w komentarzu przy każdym ignorze.

### [MEDIUM] (shell/user_service/framework/user/user/api/app.py:71 vs platform/framework/api/setup.py:61-66,91-114) — niejednolity schemat błędów; `ProblemDetail`/`setup_api_common` to martwy kod
- **Reguła:** review-api-contracts — spójny format odpowiedzi.
- **Dlaczego:** żadna fabryka aplikacji nie woła `_register_error_handlers`/`setup_api_common`; rejestrowany jest tylko `DomainError` → `{"detail": ...}`, a HTTPException/validation/unhandled wracają domyślnymi kształtami FastAPI bez correlation id.
- **Poprawka:** użyć `setup_api_common(...)` w każdej fabryce albo zarejestrować brakujące handlery i ustandaryzować błędy do `ProblemDetail`.

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

### [MEDIUM] (`StateData(JsonStr("{}"))` w mappery model_to_entity: session/workflow/project/user_state) — fallback `"{}"` jako wartość zastępcza na brak danych
- **Reguła:** no-empty-fallbacks.
- **Dlaczego:** mappery konstruują `StateData(JsonStr("{}"))`, gdy w bazie brak danych, zamiast `None` — `{}` udaje poprawny stan tam, gdzie go nie ma. (Uwaga: sam `StateData`/`JsonStr` już walidują JSON — to nie jest problem walidacji.)
- **Poprawka:** w mappery używać `None`, gdy dane są nieobecne; agregate pozwala na `StateData | None`.

---

> **False positive skreślony:** `self._id_generator_` (session_management_service) to **świadoma konwencja** testów architektury — `test_domain_services_are_stateless` traktuje atrybuty z **końcowym podkreśleniem** jako wstrzyknięte zależności (stateless service). Zmiana na `_id_generator` złamała regułę; przywrócono oryginał.

---

## Suplement: testy/CI — ustalenia dodatkowe

> Uwaga: wpis o przeniesieniu testu `session_seed` do `integration/sql_sqlite` oraz o `tests-optimistic` zostały **naprawione** (test przeniesiony, katalog usunięty) — szczegóły w notce „Naprawione".

---

## Rekomendowana kolejność napraw

1. **Bramki CI/typy** — zdjąć mypy-override dla `bootstrap/framework` (zostawić wąski tombstone dla testów); dodać uzasadnienia przy `# type: ignore` lub naprawić typowanie.
2. **Domena (pozostałe)** — DTO bez pól audytowych (`changed_at`/`deleted_at`); `StateData` bez fallbacku `{}` w mappery.
3. **API/bezpieczeństwo** — `ProblemDetail` zamiast martwego `setup_api_common`; JWT albo podpiąć w production, albo usunąć; wersjonowanie API zamiast hardkodzonego `/api/v1`.
4. **Integracja** — `GetSessionHistory` jako prawdziwy read model (snapshot) zamiast duplikatu `GetSessionById`.
5. **API/struktura** — paginacja `Page[...]` dla scheduling; keyset zamiast OFFSET+COUNT na listach.

---

*Raport wygenerowany na podstawie skilli `review-*`; każda pozycja oznaczona jest lokalizacją `file:line`, regułą i proponowaną poprawką. Ustalenia oznaczone BLOCKER/CRITICAL zweryfikowane bezpośrednio w źródłach.*