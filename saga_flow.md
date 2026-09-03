# saga_flow.md — Jak przebiega proces sagi przez obiekty, transakcje i stany

> Dokument opisuje **faktyczny, zaimplementowany przepływ** sagi na platformie SHELL
> (dedukowany z kodu: `platform/process/saga/*`, `platform/infrastructure/process/saga/*`,
> `messaging/inbox/*`, `messaging/command/*`, pilot `ProjectProvisionSaga` w `project_service`).
> Rozbicie: **stany i wszystkie przejścia** (automat), **elementy transakcyjne** (gdzie
> transakcja się zaczyna, co obejmuje, kto robi `commit`), **scenariusze** od startu do
> terminalnego stanu oraz **ścieżki idempotencji / wyścigów / awarii**.

---

## 0. Notacja i obiekty

Legenda obiektów w kolejności przepływu:

| Skrót | Obiekt | Rola |
|---|---|---|
| **Envelope** | `CommandDeliveryEnvelope` / `IntegrationEventDeliveryEnvelope` | wire JSON (kind, outbox_id, name, payload, tracing) |
| **inbox_X** | `inbox_command` / `inbox_event` | rekord delivery po stronie odbiorcy (status/lease) |
| **outbox_X** | `outbox_command` / `outbox_event` | rekord delivery u nadawcy (`published_at` NULL dopóki nie wysłane) |
| **Consumer** | `RabbitCommandInboxConsumer` / `RabbitEventInboxConsumer` | broker → wiersz inbox (własna transakcja, dedup unique `(source_service, outbox_id)`) |
| **Claim** | `InboxClaimService` | T-A: selekcja + `PROCESSING` + `claimed_by` + `lease_until` + commit (krótkie; bez zamka na czas handlera) |
| **Processor** | `CommandInboxProcessor` / `EventInboxProcessor` / `SagaTimeoutProcessor` (baza `InboxProcessorBase`) | T-B: deserializacja → dispatch → ack + commit |
| **Scope** | `DeliverySessionScope` (`ContextVar`) | ambientowa sesja procesora; handlery/UoW/outboxy/instancja sagi dzielą ją = deferred commit |
| **Bus** | `CommandBus` / `EventBus` | lokalny dispatch (sync/in-proces) |
| **Dispatcher** | `CommandDeliveryDispatcher` (port) / `SqlCommandDeliveryDispatcher` | zapis `outbox_command` na scope.session, bez commita |
| **Writer** | `SqlCommandOutboxWriter.append` | dodanie wiersza `outbox_command` (id, tracing) |
| **Relay** | `CommandOutboxToTransportRelay` (i event) | `outbox_X` → broker → `published_at` (własna transakcja) |
| **Manager** | `SagaManager` podklasa (pilot: `ProjectProvisionSagaManager`) | maszyna stanów: `start`/`on_event`/`on_timeout`/`dispatch_step`/`dispatch_compensation` |
| **SagaHandler** | np. `WorkspaceProvisionedSagaHandler` | subskrybent `EventBus` (warstwa process); `get_by_key` → `manager.on_event` |
| **Repo** | `SagaRepository` → `SqlSagaRepository` | trwałość instancji (`saga_instance`), scope-aware, optimistic locking |
| **TimeoutRepo** | `SagaTimeoutRepository` → `SqlSagaTimeoutRepository` | `schedule`/`cancel` rekordów `saga_timeout` (`InboxStateMixin`) |
| **TimeoutProcessor** | `SagaTimeoutProcessor` (podklasa `InboxProcessorBase`, model=`saga_timeout`) | claim z `next_attempt_at=due_at` → `SagaTimedOut` na EventBus → ack |
| **UoW** | `UnitOfWork` (handler-side) | transakcja handlera; w scope = deferred (flush, commit robi processor) |

Kluczowe reguły:

- **Jedna typologia komendy**: nie ma osobnych Async/ProcessCommand — intencja to `Command`.
- **Komendy delivery produkuje wyłącznie warstwa process (saga)**; aplikacja ich nie dispatchuje.
- **Krok sagi NIGDY nie jest transakcją wielo-serwisową** — każdy krok to delivery
  (at-least-once), a atomowość obowiązuje tylko **wewnątrz jednego BC** (jeden rekord inbox).
- Kontrolerem atomowości w T-Process jest **`DeliverySessionScope`**: handler + jego UoW +
  zapisy wystawiające (`outbox_*`, instancja sagi, `saga_timeout`) dzielą sesję procesora →
  **jeden `commit`**; `UoW` w scope **nie commituje**.
- Instancja sagi jest **immutable snapshotem** (`SagaInstance`, frozen dataclass). Każde
  przejście stanu = `create` (v1) albo `update` (version+1) z optimistic locking.
- **Idempotencja przejść** = guard na `(status, current_step, saga_id)` + optimistic `version` +
  (na torze zewn.) unique `(source_service, outbox_id)` / `processed_delivery`.

---

## 1. `SagaInstance` — pola i semantyka zapisu

```
saga_id        primary key (UUID instancji, nie biznesowy)
saga_type      "project_provision" (SAGA_TYPE)
saga_key       klucz biznesowy (pilot: project_id)
status         SagaStatus: running | failing | compensating | compensated | completed
current_step   "provision_workspace" | "compensation:provision_workspace" | None
business_payload  dict (pilot: {"project_id": ...})
completed_steps   tuple (kroki zakończone sukcesem)
failed_steps      tuple (kroki oznaczone porażką)
version        int, start od 1; co update +1 (warunek optimistic)
created_at / updated_at / completed_at / failed_at / compensated_at
```

- `create` → wiersz z `version=1`, `status=RUNNING`.
- `update` → `UPDATE ... WHERE id=... AND version=<stary>`; 0 wierszy ⇒
  `ConcurrentModificationError("Saga", saga_id)`. Rowversion rośnie w bazie (`version+1`).
- Wszystkie zapisy scope-aware: w scope — bez commita (absorbuje je T-Process); poza scope —
  własna sesja + commit (tryb standalone).

---

## 2. Automat stanów — wszystkie przejścia

Obsługiwane wejścia: komenda `StartProjectProvisionCommand` (start delivery), faktu
`WorkspaceProvisioned` / `WorkspaceProvisionFailed` / `WorkspaceReleased` (przez `EventBus`),
sygnał `SagaTimedOut` (przez `EventBus` z `SagaTimeoutProcessor`).

```
[brak instancji]
   │ StartProjectProvisionCommand (guard: get_by_key == None)
   ▼
 RUNNING  (current_step=provision_workspace)
   │  WorkspaceProvisioned (guard: RUNNING && current_step=provision_workspace)
   ▼
 COMPLETED  (current_step=None)                    ── terminal
   │
   │  WorkspaceProvisionFailed / SagaTimedOut (guard: RUNNING && current_step=provision_workspace)
   │        ├─ jeśli krok ma kompensację (compensation_command i (completed | compensate_on_failure))  → ▼
   │        └─ w przeciwnym razie                                                                      → ▼ (COMPENSATED bezpośrednio)
   ▼
 COMPENSATING (current_step=compensation:provision_workspace)
   │  WorkspaceReleased (guard: COMPENSATING && current_step=compensation:...)
   ▼
 COMPENSATED (current_step=None)                  ── terminal

Każda inna kombinacja (guard nieprzechodzący / brak instancji / niewłaściwy saga_id)
 = no-op (idempotentne odrzucenie, bez zapisu).
```

### 2.1 Tabela przejść (kompletna)

| # | Wejście | Otwiera | Guard (wszystkie muszą przejść) | Mutacja instancji | Efekty uboczne (scope) | version | Sygnatury |
|---|---|---|---|---|---|---|---|
| T1 | `StartProjectProvisionCommand` | `StartProjectProvisionHandler` → `manager.start` | `get_by_key(project_provision, project_id) is None` | `create`: `RUNNING`, `current_step="provision_workspace"`, `business_payload={"project_id": ...}` | **outbox** `ProvisionWorkspaceCommand(project_id, fail)`; `schedule(saga_timeout)` **tylko jeśli `step.timeout`** (pilot: brak → nie) | 1 (nowa) | created_at |
| T2 | `WorkspaceProvisionedIntegrationEvent` (sukces kroku) | `WorkspaceProvisionedSagaHandler` → `on_event` | `exists` ∧ `RUNNING` ∧ `current_step="provision_workspace"` | `update`: `COMPLETED`, `current_step=None`, `completed_steps += ("provision_workspace",)` | `timeouts.cancel(saga_id, "provision_workspace")` (PENDING/RETRY→PROCESSED) | +1 | completed_at |
| T3 | `WorkspaceProvisionFailedIntegrationEvent` (porażka, jest kompensacja) | `WorkspaceProvisionFailedSagaHandler` → `on_event` | `exists` ∧ `RUNNING` ∧ `current_step="provision_workspace"` ∧ `compensation_command` i (`failed_step ∈ completed_steps` ∨ `compensate_on_failure`) | `update`: `COMPENSATING`, `current_step="compensation:provision_workspace"`, `failed_steps += ("provision_workspace",)` | **outbox** `ReleaseWorkspaceCommand(project_id)` (kompensacja) | +1 | failed_at |
| T4 | `WorkspaceProvisionFailedIntegrationEvent` (porażka, brak kompensacji) | `WorkspaceProvisionFailedSagaHandler` → `on_event` | `exists` ∧ `RUNNING` ∧ `current_step="provision_workspace"` ∧ warunek kompensacji NIESPEŁNIONY | `update`: `COMPENSATED` od razu, `current_step=None`, `failed_steps += ...` | bez outboxa | +1 | failed_at, compensated_at |
| T5 | `SagaTimedOut` (timeout kroku) | `SagaTimeoutProcessor` → `EventBus` → `ProjectProvisionTimeoutHandler` → `on_timeout` | `exists` ∧ `saga_id == event.saga_id` ∧ `RUNNING` ∧ `current_step == event.step` | deleguje do **T3** (kompensacja) albo **T4** (bez) z `failed_step=event.step`, `expected_saga_id` | jak T3/T4 | +1 | jak T3/T4 |
| T6 | `WorkspaceReleasedIntegrationEvent` (kompensacja wykonana) | `WorkspaceReleasedSagaHandler` → `on_event` | `exists` ∧ `COMPENSATING` ∧ `current_step="compensation:provision_workspace"` | `update`: `COMPENSATED`, `current_step=None` | bez outboxa | +1 | compensated_at (failed_at zachowane) |
| T7 | Jakiekolwiek inne | odpowiedni handler | guard NIE przechodzi (brak instancji / zły status / zły `current_step` / zły `saga_id`) | **no-op, brak zapisu** | — | — | — |
| T8 | `StartProjectProvisionCommand` duplikat | `StartProjectProvisionHandler` | `get_by_key(...) is not None` | **no-op** (nie tworzy nowej instancji) | — | — | — |

Uwagi do przejść:

- **T2 vs T5 wyścig**: timeout i rezultat konkurują. Którekolwiek wygra (pierwsze przejdzie
  guard i zajmie `version`), drugie po retry/ponownym odczycie napotka **zmieniony status** i
  guard odrzuci je no-op (T7). Spóźniony rezultat po timeout/kompensacji nie nadpisuje stanu.
- **Fakt = kanał wewnętrzny**: w pilocie rezultat kroku wraca **in-process** `EventBus`
  w tej samej transakcji co handler kroku (T-Process uczestnika). Alternatywny wariant —
  fakt przez `outbox_event` + `T-Process` event-inbox — daje aktualizację sagi w oddzielnej
  transakcji (opisany w scenariuszach).
- **Kompensacja NIE anuluje timeoutu**: `_fail` (T3/T5) nie woła `timeouts.cancel` (robi to
  tylko `_complete` T2). Timeout, który odpali się później, zostanie odrzucony guardem
  `RUNNING`/`current_step` (T7). Wiersz `saga_timeout` zostaje zacknowledge'owany przez
  procesor mimo odrzucenia.
- Pilot: krok `provision_workspace` ma `compensation_command=ReleaseWorkspaceCommand` i
  `compensate_on_failure=True` → **T4 (porażka bez kompensacji) jest dla pilota nieosiągalny**
  (zawsze kompensuje). T4 pozostaje zachowaniem platformy.
- Pilot nie definiuje `timeout` w `StepDefinition` → **T5 (timeout) jest zdolnością platformy**;
  w pilocie nie powstają rekordy `saga_timeout`.

Obserwowane `version` w pilocie (test `test_project_provision_saga`):
sukces start→v1, complete→v2; porażka start→v1, `_fail`→v2 (COMPENSATING), `_complete_compensation`→v3 (COMPENSATED).

---

## 3. Elementy transakcyjne (mapa globalna)

| Id | Nazwa | Zawartość (wszystko w JEDNEJ transakcji) | Gdzie zaczyna się | Gdzie kończy (commit) | Uwagi |
|---|---|---|---|---|---|
| **T-Local** | Komenda lokalna (API/CLI) | `CommandBus → Handler → UoW → agregat → eventy` | wejście handlera (`async with unit_of_work`) | `unit_of_work.commit()` / `__aexit__` | tylko gdy brak scope; efekt+outbox atomowo |
| **T-Claim** | Claim rekordu inbox / timeout | `SELECT (PENDING\|RETRY z next_attempt_at<=now \| PROCESSING z lease<now) → UPDATE PROCESSING + claimed_by + lease_until` | `InboxClaimService.claim_batch` | `session.commit()` claima | krótka; bez zamka na czas handlera; re-claim po wygaśnięciu lease (`lease_duration_seconds`) |
| **T-Process** | Przetwarzanie rekordu inbox/timeout | `validation → deserializacja → dispatch → efekt handlera + outbox_* + instancja sagi + ack PROCESSED` | otwarcie sesji w `_process_in_transaction` | `session.commit()` procesora | JEDEN commit; wyjątek → `_schedule_failure` (RETRY/DLQ); duplikat `outbox_id` → ack i skip |
| **T-Relay** | Publikacja outboxa | `SELECT published_at IS NULL → deliver(envelope) → UPDATE published_at` | otwarcie sesji w `relay.run_once` | `session.commit()` relaya | ryzyko powtórzenia (crash między publish a commit) — łagodzi dedup konsumenta |
| **T-Consumer** | Broker → inbox | `INSERT wiersz inbox (on_conflict_do_nothing) → ack` | `_persist` | `session.commit()` konsumenta | dedup unique `(source_service, outbox_id)` |
| **T-Instance** | Zapis stanu sagi (repo) | w scope: gest instancji (`create`/`update` z optimistic `version`), **bez commita** = część T-Process; poza scope: własna sesja + commit | `SqlSagaRepository.create/update/get_by_key` | scope: nic (commit procesora); standalone: `commit()` repo | `version`+warunkowy UPDATE; konflikt → `ConcurrentModificationError` |
| **T-Timeout** | Zapis timeoutu | `schedule`: INSERT `saga_timeout(PENDING, due_at, next_attempt_at=due_at)`; `cancel`: UPDATE PENDING/RETRY→PROCESSED — scope (część T-Process) albo własna sesja | `SqlSagaTimeoutRepository.schedule/cancel` | jak T-Instance | `saga_timeout` = rekord przetwarzany jak inbox (`SagaTimeoutProcessor`) |

**Zasada „commit owner”**: T-Claim/T-Consumer/T-Relay i T-Process mają **własnego właściciela
commit**. T-Process jest **nadrzędny** dla wszystkiego, co dzieje się wewnątrz jego sesji:
jeśli handler wejdzie w UoW, to UoW **nie commituje** (deferred) — commituje procesor po ack.
Crash między wykonaniem handlera a commitem procesora = brak ack = rekord wróci do retry
(claim + zabezpieczenie lease) i T-Process powtórzy się at-least-once z idempotencją guardów.

### 3.1 Cykl życia rekordu `saga_timeout` (gdy `step.timeout` ustawiony)

```
schedule (T-Process kroku / standalone): PENDING, due_at=now+due_in, next_attempt_at=due_at
  ↓ (wait)
T-Claim (SagaTimeoutProcessor): PENDING (next_attempt_at<=now) → PROCESSING+lease → commit
T-Process (SagaTimeoutProcessor):
  deserialize → SagaTimedOut(saga_id, saga_key, step)
  → EventBus.publish([SagaTimedOut])
      → ProjectProvisionTimeoutHandler → manager.on_timeout → T5 (guard → T3/T4)
  → ack PROCESSED → commit
  wyjątek przy publish → RETRY z backoff (exp. 30s*2^(n-1)+jitter) → max_retries → DEAD_LETTER
cancel (T2, gdy krok się powiódł): PENDING/RETRY → PROCESSED (nie odpali)
```

---

## 4. Scenariusze przepływu

### Scenariusz A — Start sagi komendą-inicjalizatorem (delivery)

> `StartProjectProvisionCommand` wchodzi do `project_service` jako komenda delivery
> (producent: CLI / zewnętrzny BC / inna saga przez `CommandDeliveryDispatcher`).

```
NADAWCA (zewnętrzny BC / CLI / inna saga)
  CommandDeliveryDispatcher.dispatch(StartProjectProvisionCommand, target="project")  [T-Process nadawcy]
    → SqlCommandOutboxWriter.append → outbox_command(published_at=NULL)               (część T-Process nadawcy)

Relay  CommandOutboxToTransportRelay.run_once                                          [T-Relay]
  select outbox → deliver(envelope, routing "command.StartProjectProvisionCommand") → Rabbit
  → UPDATE published_at → commit

Consumer  RabbitCommandInboxConsumer._persist                                          [T-Consumer]
  decode → INSERT inbox_command(source_service, outbox_id...) → commit → ack

Processor  CommandInboxProcessor:
  T-Claim  InboxClaimService.claim_batch → PROCESSING + lease → commit                 [T-Claim]
  T-Process CommandBus.dispatch(StartProjectProvisionCommand)                          [T-Process]
    → StartProjectProvisionHandler
        guard: get_by_key("project_provision", project_id) — jeśli istnieje → return (T8)
        manager = manager_factory(project_id)
        manager.start(project_id, fail):
          instance = SagaInstance(RUNNING, current_step="provision_workspace",
                                  business_payload={"project_id": project_id}, version=1)
          repository.create(instance)                                                  (scope, bez commita)  [T-Instance]
          dispatch_step(step="provision_workspace", ProvisionWorkspaceCommand(project_id, fail))
            → SqlCommandDeliveryDispatcher → outbox_command(provision_workspace)       (scope, bez commita)
            → (jeśli step.timeout) SqlSagaTimeoutRepository.schedule                   (scope, bez commita)  [T-Timeout]
    → ack PROCESSED
  → session.commit()   ← JEDNA transakcja: instancja RUNNING (v1) + outbox_command kroku + ack
```

### Scenariusz B — Krok + kompletacja (sukces)

> Uczestnik obsługuje `ProvisionWorkspaceCommand`, publikuje fakt `WorkspaceProvisioned`,
> saga reaguje i kończy instancję.

```
Relay → Rabbit → Consumer → inbox_command(ProvisionWorkspaceCommand)         [T-Relay][T-Consumer]
CommandInboxProcessor:
  T-Claim                                                                [T-Claim]
  T-Process CommandBus.dispatch(ProvisionWorkspaceCommand)                [T-Process]
    → ProvisionWorkspaceHandler (application, uczestnik)
        → EventBusPublisher.publish([WorkspaceProvisionedIntegrationEvent])
            → EventBus.publish (sekwencyjnie, ten sam wątek/sesję)         [in-process]
                → WorkspaceProvisionedSagaHandler
                    → guard: instance? None → no-op (T7)
                    → manager = factory(project_id, saga_id=instance.saga_id)
                    → on_event(event) → T2:
                        instance = get_by_key(SAGA_TYPE, project_id)                          (scope)
                        guard: RUNNING ∧ current_step="provision_workspace"?
                        timeouts.cancel(saga_id, "provision_workspace")                       (scope)
                        repository.update(SagaInstance(COMPLETED, current_step=None,
                                              completed_steps+=("provision_workspace",),
                                              version=instance.version))                      (scope)  [T-Instance v→v+1]
    → ack PROCESSED
  → session.commit()   ← JEDNA transakcja: efekt uczestnika + stan sagi COMPLETED (v2) + ack
```

### Scenariusz C — Porażka kroku + kompensacja + zamknięcie

> Uczestnik publikuje `WorkspaceProvisionFailed`, saga przechodzi w kompensację,
> kompensacja wykonuje się jako osobna delivery i domyka instancję do `COMPENSATED`.

```
Relay → Rabbit → Consumer → inbox_command(ProvisionWorkspaceCommand)         [T-Relay][T-Consumer]
CommandInboxProcessor:
  T-Claim                                                                [T-Claim]
  T-Process CommandBus.dispatch(ProvisionWorkspaceCommand)                [T-Process]
    → ProvisionWorkspaceHandler (fail=True)
        → EventBus.publish([WorkspaceProvisionFailedIntegrationEvent])
            → WorkspaceProvisionFailedSagaHandler → on_event → T3:
                guard: RUNNING ∧ current_step="provision_workspace"?
                step.compensation_command=ReleaseWorkspaceCommand ∧ compensate_on_failure=True
                repository.update(COMPENSATING,
                                  current_step="compensation:provision_workspace",
                                  failed_steps+=("provision_workspace",))
                dispatch_compensation(step, ReleaseWorkspaceCommand(project_id))
                  → outbox_command(ReleaseWorkspaceCommand)                (scope)
    → ack PROCESSED
  → session.commit()   ← JEDNA: stan COMPENSATING (v2) + outbox kompensacji + ack
                                            │
                                            ▼  (osobny tor delivery, at-least-once)
[dalszy przepływ kompensacji]
Relay → Rabbit → Consumer → inbox_command(ReleaseWorkspaceCommand)          [T-Relay][T-Consumer]
CommandInboxProcessor: Claim + T-Process
    → ReleaseWorkspaceHandler → EventBus.publish([WorkspaceReleasedIntegrationEvent])
        → WorkspaceReleasedSagaHandler → on_event → T6:
            guard: COMPENSATING ∧ current_step="compensation:provision_workspace"?
            repository.update(COMPENSATED, current_step=None, compensated_at=now,
                              version=instance.version)                     [T-Instance v→v+1]
    → ack PROCESSED
  → session.commit()   ← JEDNA: efekt kompensacji + stan COMPENSATED (v3) + ack
```

### Scenariusz C′ — Porażka bez kompensacji (zachowanie platformy; w pilocie nieosiągalne)

Jeśli w `StepDefinition` nie ma `compensation_command`, albo krok nie jest w
`completed_steps` i `compensate_on_failure=False`, to `_fail` (T4) **bezpośrednio** ustawia
`COMPENSATED` (`current_step=None`, `failed_at`, `compensated_at`) — bez wystawiania
komendy kompensacji. Wszystko nadal w jednym T-Process.

### Scenariusz D — Timeout kroku → kompensacja (zdolność platformy)

Wymaga `StepDefinition.timeout` (pilot go nie definiuje). Przebieg dla realistycznej sagi:

```
W momencie startu kroku (T-Process, scenariusz A):
  manager.dispatch_step(step, cmd)
    if step.timeout:
      SqlSagaTimeoutRepository.schedule(saga_id, saga_key, step, due_in)
        → INSERT saga_timeout(PENDING, due_at, next_attempt_at=due_at, ...)   (scope)  [T-Timeout]

PÓŹNIEJ (worker extra_processors / run_delivery_workers):
  SagaTimeoutProcessor (podklasa InboxProcessorBase, model=saga_timeout):
    T-Claim  claim PENDING/RETRY z next_attempt_at<=now → PROCESSING+lease → commit     [T-Claim]
    T-Process deserialize → SagaTimedOut(saga_id, saga_key, step)                       [T-Process]
        → EventBus.publish([SagaTimedOut])
            → ProjectProvisionTimeoutHandler
                → guard: instance? None / saga_id niezgodny → no-op (T7)
                → manager.on_timeout(event) → T5:
                    guard: RUNNING ∧ current_step == event.step ∧ saga_id == event.saga_id?
                    → _fail(failed_step=event.step, expected_saga_id=event.saga_id)
                        → T3 (kompensacja: COMPENSATING + outbox ReleaseWorkspace) lub
                        → T4 (COMPENSATED bezpośrednio)                                  (scope)
        → ack PROCESSED → commit (efekt + ack)
  // wyjątek przy publish → _schedule_failure: RETRY(backoff) → po max_retries → DEAD_LETTER
```

Wyścig timeout–rezultat: patrz T2 vs T5 w §2.1 (guard odrzuca spóźniony rezultat).

### Scenariusz E — Start sagi po fakcie (event) — wzorzec platformy

> Gdy inicjator nie może dispatchować komendy delivery (reguła warstwy aplikacji) —
> start przez fakt skorelowany trasą `EventRoute(on_new_instance=True)`.

```
Aplikacja (handler) → stage_events/publish faktu (np. ProjectProvisionRequestedIntegrationEvent)
  → outbox_event                                                                  (część T-Process/T-Local nadawcy)
Event relay → Rabbit → consumer → inbox_event                                      [T-Relay][T-Consumer]
EventInboxProcessor: Claim + T-Process
  → EventBus.publish → saga start handler (process) → manager.start(...)
      → NOWA instancja RUNNING (v1) + dispatch kroku (outbox_command)              (scope)
  → ack → commit (instancja + outbox krok + ack)
```

W pilocie start realizowany jest komendą delivery (Scenariusz A); `EventRoute` +
`on_new_instance` jest mechanizmem platformy dla przyszłych sag.

---

## 5. Scenariusz F — Idempotencja, wyścigi i duplikaty

Wszystkie ochrany wynikają z guardów (T7) + optimistic locking + dedup na torze:

| Sytuacja | Mechanizm | Efekt |
|---|---|---|
| Duplikat `StartProjectProvisionCommand` | guard `get_by_key is not None` (T8) | no-op, brak drugiej instancji |
| Duplikat `WorkspaceProvisioned` po COMPLETED | guard `RUNNING` (T7) | no-op |
| `WorkspaceProvisioned` po COMPENSATING/COMPENSATED (spóźniony sukces) | guard `RUNNING` (T7) | no-op |
| `WorkspaceProvisionFailed` po COMPLETED | guard `RUNNING` (T7) | no-op |
| `WorkspaceReleased` po COMPENSATED / po RUNNING | guard `COMPENSATING` (T7) | no-op |
| Duplikat envelowpy na brockerze (crash relay między publish a commit) | unique `(source_service, outbox_id)` w `_persist` (T-Consumer) | drugi insert pominięty |
| Ponowna dostawa na procesorze | `_is_duplicate` (processed_delivery, gdy skonfigurowane) → ack i skip w `_process_in_transaction` | brak powtórzenia handlera |
| Reclaim po awarii mid-processing | lease `lease_until` wygasa → `claim_batch` bierze rekord ponownie | at-least-once + guards |
| Dwa zdarzenia konkurujące w różnych transakcjach (np. timeout vs rezultat) | oba czytają `version=N`; jeden zrobi `UPDATE` cel, drugi dostanie `ConcurrentModificationError` → `_schedule_failure` (retry) → ponowny odczyt zmienionego stanu → guard (T7) | przetworzenie co najwyżej raz |
| Kompensacja i fakt idą inwersyjnie (release→COMPENSATING vs released→COMPENSATED) | sekwencja guardów `RUNNING`→`COMPENSATING` i `current_step` | stan i tak domyka się deterministycznie |

---

## 6. Scenariusz G — Ścieżki awarii i retry

| Awaria | Gdzie | Zachowanie |
|---|---|---|
| Wyjątek w handlerze kroku/eventu (np. `ConcurrentModificationError`, błąd agregatu) | `_process_in_transaction` → `except` | **rollback T-Process** (scope.rolled_back również) → `_schedule_failure`: `RETRY` z backoff (`retry_backoff_seconds * 2^(n-1)` + jitter) → po `max_retries` `DEAD_LETTER` |
| `scope.rolled_back` (handler jawnie wycofał UoW) | po dispatch | jak powyżej `HANDLER_ERROR: Handler rolled back its unit of work` |
| Nieobsługiwany schema_version / zła koperta | walidacja `EnvelopeValidator` | `UNSUPPORTED_SCHEMA_VERSION` → natychmiast DEAD_LETTER; inne błędy envelowpy → RETRY/DLQ |
| Błąd deserializacji | `_deserialize` zwraca None | `DESERIALIZATION_ERROR` → RETRY/DLQ |
| Błąd publish w `SagaTimeoutProcessor` | `_dispatch` → EventBus | RETRY z backoff → DLQ (test `test_publish_failure_retries_then_dlq`) |
| Broker nieosiągalny w relayu | T-Relay | `published_at` bez setu → rekord zostaje; ponowna próba w następnym `run_once` |
| Crash między broker publish a commit (relay) | T-Relay | ryzyko podwójnej wysyłki — łagodzi dedup konsumenta (§5) |
| Lease utracona podczas długiego handlera | heartbeat (gdy włączony) | przerywa dispatch, rekord re-claim po wygaśnięciu; koniec z ack nie zostaje zrobiony |
| Crash po claimu, przed handlerem | T-Claim → T-Process | lease wygasa w `lease_duration_seconds` → reclaim → przetworzenie od nowa |

---

## 7. Gdzie zaczyna się i kończy każda transakcja — podsumowanie

| # | Transakcja | Początek | Koniec (commit) | Obiekty objęte |
|---|---|---|---|---|
| 1 | **T-Local** (komenda sync API/CLI) | `async with unit_of_work` handlera | `commit()` UoW | agregat, eventy, outbox (efekt lokalny) |
| 2 | **T-Claim** (inbox / timeout) | `InboxClaimService.claim_batch` | `commit()` claima | inbox_X / saga_timeout: PROCESSING+lease |
| 3 | **T-Process** (inbox / timeout) | `_process_in_transaction` (otwarcie sesji procesora) | `session.commit()` procesora | **efekt handlera + outbox_* + instancja sagi + ack PROCESSED** |
| 4 | **T-Relay** (event/command) | `relay.run_once` (otwarcie sesji) | `commit()` relaya | outbox_X: deliver → published_at |
| 5 | **T-Consumer** (broker→inbox) | `_persist` (otwarcie sesji) | `commit()` konsumenta | wiersz inbox + ack |
| 6 | **T-Instance** (repo sagi) | wywołanie `create/update/get_by_key` | scope: braku commita (wchłonięte przez T-Process); standalone: `commit()` repo | saga_instance: upsert z `version` |
| 7 | **T-Timeout** (timeout sagi) | wywołanie `schedule/cancel` | scope: braku commita; standalone: `commit()` repo | saga_timeout: INSERT / PENDING→PROCESSED |

**Najważniejsze do zapamiętania:**
- **W obrębie jednego BC** stan sagi + zlecone delivery + ack to **jedna transakcja**
  (T-Process) dzięki `DeliverySessionScope` (deferred commit).
- **Między BC** nie ma jednej transakcji: każda hop (relay, consumer, T-Process odbiorcy)
  to osobna transakcja → **at-least-once**; idempotencję dają unique
  `(source_service, outbox_id)` + `processed_delivery` + guards + optimistic `version`.
- Saga **nigdy** nie utrzymuje otwartej transakcji na czas oczekiwania — stan jest trwałym
  rekordem (`saga_instance`), a postęp przez osobne delivery; każdy krok kończy się w stanie
  terminalnym (`COMPLETED` albo `COMPENSATED`), a każdy inny sygnał jest no-op.
- Transition matrix to kontrakt: **T1–T6** to jedyne przejścia modyfikujące, **T7/T8** to
  jedyne dozwolone odrzucenia — żadnego innego efektu ubocznego nie ma.

---

## 8. Pliki referencyjne

- `platform/process/saga/base/saga_manager.py` — `dispatch_step`/`dispatch_compensation` (scheduler timeoutu przy `step.timeout`)
- `platform/process/saga/base/saga_state.py` — `SagaStatus`, `SagaState`
- `platform/process/saga/saga_instance.py` — immutable snapshot
- `platform/process/saga/saga_timed_out.py` — sygnał timeoutu
- `platform/process/saga/steps.py` — `StepDefinition`/`StepRegistry`
- `platform/process/saga/correlation/{saga_registry,event_route}.py` — trasy event→saga (`on_new_instance`)
- `platform/process/saga/ports/{saga_repository,saga_timeout_repository,command_delivery_dispatcher}.py`
- `platform/infrastructure/process/saga/` — `SqlSagaRepository`, `SqlSagaTimeoutRepository`,
  `SagaTimeoutProcessor`, `command_delivery.py`, `models/saga_delivery.py`
- `platform/infrastructure/messaging/inbox/inbox_processor_base.py`,
  `inbox_claim_service.py` — cykl claim→process→ack→retry/DLQ, dedup, lease
- `platform/infrastructure/messaging/command/{sql_command_outbox_writer,command_transport}`
- `platform/infrastructure/messaging/event/event_worker.py` (`run_delivery_workers`, `extra_processors`)
- Pilot: `shell/project_service/process/project/project_provision/` (manager, steps, state,
  handlery) + `application/project/project_provision/` (handlery uczestnika, eventy, komendy)
- Testy: `shell/tests/project_service/unit/process/test_project_provision_saga.py`
  (sukces, porażka+kompensacja, wersjonowanie) oraz
  `shell/tests/platform/integration/sql_sqlite/test_saga_timeout_processor.py`
  (fire/nie-fire/retry/DLQ timeoutu)