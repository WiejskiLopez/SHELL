# Wsparcie dla procesów Saga na platformie SHELL

## Cel dokumentu

**Typ dokumentu**: dokument projektowy (design / propozycja rozszerzenia platformy),
nie specyfikacja implementacyjna ani tutorial.

**Cel główny**: zaprojektowanie pełnego, enterprise wsparcia dla wzorca **Saga /
Process Manager (orkiestracja)** na platformie SHELL — tak, aby bounded contexty
mogły implementować długotrwałe, wieloagregatowe i wielo-BC procesy biznesowe
wspólnie, zgodnie z regułami architektonicznymi projektu (zero wyjątków od
konwencji warstw, dyscyplina cross-aggregate, outer/inner dependency rules).

**Kontekst i przesłanka**: platforma SHELL ma już gotowe mechanizmy
transakcyjnego outbox/inbox (dla eventów i komend), współdzieloną transakcję
handler–processor (`DeliverySessionScope` + deferred commit), tracing
`correlation_id`/`causation_id`, `PollingWorker`, kontrakty komend i DI per BC.
Brakuje natomiast warstwy `process/`, która jest przewidziana w architekturze
(skille, testy `test_process_structure__*`) i jest naturalnym domem dla sag.

**Kluczowa decyzja przyjęta w tym dokumencie**: **komenda jest jednym typem** —
nie wyróżniamy `ProcessCommand`/`SagaCommand`. Synchronizm/asynchronizm to
własność **transportu i kontekstu**, nie klasy. Rola komendy (zwykła operacja
aplikacji vs inicjalizator sagi) wynika z **rejestracji** — tego, gdzie i z jakim
handlerem dana komenda jest zarejestrowana w danym serwisie.

**Zakres dokumentu** — co opisuje:
1. Analiza stanu obecnego platformy: co już istnieje do reużycia, a czego brakuje.
2. Docelowy model: **jeden typ komendy**, rola przez rejestrację (aplikacja =
   komenda lokalna; process = inicjalizator sag i kroki delivery), wyniki przez eventy.
3. Przepływ pilota sagi: komenda inicjatora → instancja → krok delivery →
  rezultat i potwierdzona kompensacja; pełny model platformowy jest opisany jako
  docelowy i częściowo zaimplementowany.
4. **Migrację** z obecnego stanu (usunięty marker `ProcessCommand`, port
  `CommandDeliveryDispatcher` w `platform/process/saga/ports/`, reguła
  "dispatch delivery tylko z process/").
5. Trwałość stanu (`saga_instance`), korelacja, kompensacje, timeouty, observability,
   DI/Composition Root, testy (architektura, unit, integracja) i plan wdrożenia.

**Dla kogo**: architekci i developerzy rozwijający platformę SHELL oraz bounded
contexty — dokument jest punktem odniesienia przy implementacji pierwszej sagi.

**Poza zakresem**: nie zawiera gotowego kodu produkcyjnego (tylko szkice), nie
definiuje konkretnych sag biznesowych, nie opisuje pełnej choreografii eventowej,
nie rozstrzyga ostatecznie decyzji z sekcji 9 (wskazuje rekomendacje), nie
obejmuje read-side modeli sag.

**Stan dokumentu**: propozycja docelowa z zaimplementowanym pilotem
`ProjectProvisionSaga`. Ostateczną wyrocznią poprawności jest kod produkcyjny
oraz testy; elementy oznaczone jako roadmap nie są jeszcze kontraktem platformy.

---

## 1. TL;DR (wnioski)

1. **Platforma ma już fundamenty** dla sag: transactional outbox/inbox (eventy i
   komendy) z lease+retry+DLQ, współdzielona transakcja handler–processor
   (`DeliverySessionScope` + deferred commit), tracing `correlation_id`/`causation_id`,
   `PollingWorker`, kontrakty komend, DI per BC.
2. **Jeden typ komendy** (`Command`). Nie istnieje `ProcessCommand`/`SagaCommand`.
   Rola komendy wynika z **rejestracji** w danym serwisie:
   - zarejestrowana z handlerem w warstwie **aplikacji** → **komenda lokalna**
     (obsłużona w jednej transakcji),
   - zarejestrowana jako **start handler** w warstwie **process** → **inicjalizator sagi**
     (każde wystąpienie tworzy nową instancję),
   - dispatchowana przez proces do uczestnika → **komenda delivery** (at-least-once
     przez `outbox_command`, obsłużona lokalnie w serwisie docelowym).
3. **Słownik**: zamiast "synchroniczna/asynchroniczna komenda" używamy
   **komenda lokalna** (jedna transakcja) i **komenda delivery** (transport
   outbox→inbox, wiele transakcji). Saga jest z natury wielowątkowa/multi-transakcyjna,
   więc "sync/async" jest kategorią transportu, nie typu.
4. **Migracja jest czysta**: marker `ProcessCommand` został usunięty, a port
  `CommandDeliveryDispatcher` należy do `platform/process/saga/ports/`. Pilot
  `ProjectProvisionSaga` jest producentem komend delivery przez proces, nie przez
  warstwę aplikacji.
5. **Wsparcie platformowe jest częściowe**: istnieją wspólne mechanizmy
  persistence, dispatchu i timeoutów, natomiast pełna korelacja przez
  `SagaRegistry`, metryki, readiness i obsługa DLQ pozostają roadmapą.
6. **Directory layout**: sagi per BC w `shell/<bc>_service/process/<bc>/<saga>/`,
   budulce w `shell/platform/process/saga/`, adaptery SQL w
   `shell/platform/infrastructure/process/saga/`.

---

## 2. Analiza stanu obecnego

### 2.1 Co platforma już udostępnia — weryfikacja end-to-end

Analiza kodu pokazuje, że nie wszystko, co "istnieje", działa dziś przepływowo.
Dzielimy to na **a) sprawdzone do reuse** i **b) niepełne / generujące problemy —
kandydaci do refaktoryzacji (etap 0)**. Pozycje z (b) NIE są ramami brzegowymi
(§9.2) — to błędy do naprawy, żeby tor delivery mógł w ogóle działać.

#### a) Sprawdzone do reuse (baseline)

| Mechanizm | Gdzie | Przydatność dla sagi |
|---|---|---|
| `Command` (marker) | `platform/application/command/command.py` | **jedyny typ komendy** |
| `CommandBus` | `platform/application/bus/command_bus.py` | local dispatch; rejestracja handlerów (również start handlerów sagi) |
| `EventBus` (subscribe/publish) | `platform/application/bus/event_bus.py` | dotarcie eventów/rezultatów do sagi |
| `CommandDeliveryModels` (`outbox_command`/`inbox_command`) | `platform/infrastructure/persistence/sql/models/command_delivery.py` | tabele transportu komend delivery (unicast, `target_service`) |
| `CommandInboxProcessor` | `platform/infrastructure/messaging/command/processor/command_inbox_processor.py` | dostarczenie komendy delivery do lokalnego handlera (`CommandBus`) — strona odbioru jest owiredowana |
| `InboxProcessorBase` (claim→process→ack, lease, retry, DLQ, heartbeat) | `platform/infrastructure/messaging/inbox/inbox_processor_base.py` | procesowanie eventów/komend i timeoutów sagi |
| `InboxStateMixin` / `InboxStatus` | `platform/infrastructure/persistence/sql/models/mixins/inbox_state.py`, `platform/domain/value_objects/inbox_status.py` | stany operacyjne rekordów (też `saga_timeout`) |
| `DeliverySessionScope` + deferred commit UoW | `platform/application/context/session_scope.py`, `persistence/sql_alchemy_uow_base.py:117-153` | **jedna transakcja** na event sagi: stan + outbox + ack |
| Tracing `correlation_id`/`causation_id` | `platform/doc/tracing-context.md` | łączy wszystkie kroki sagi w jeden flow |
| `CommandContract`, katalog kontraktów | `platform/application/contracts/command_contract.py`, `contract_catalog.py` | wersjonowany kontrakt wire dla komend delivery |
| `PollingWorker`, `WorkerHeartbeatRecorder`, `run_delivery_workers` | `platform/infrastructure/messaging/polling_worker.py`, `event/event_worker.py` | workery sagi (w tym timeout) |
| Fabryki modeli delivery per BC | `platform/infrastructure/persistence/sql/models/command_delivery.py` | wzorzec dla `build_saga_delivery_models` |
| DI: `dependency_injector` + `configure_*` per BC | np. `session_service/bootstrap/session/container/session_core_container.py` | wzorzec rejestracji sag |
| Metryki (`MetricsBackend`), readiness | `platform/observability/` | observability sag |

#### b) Stan i ograniczenia implementacji

1. **Tor komend delivery jest podłączony dla pilota projektu.**
  `ProjectCoreContainer` rejestruje dispatcher, kontrakty i `CommandOutboxToTransportRelay`,
  a `project_service` uruchamia relay razem z workerem. Pełny przepływ RabbitMQ nadal
  wymaga testu systemowego; pozostałe BC należy podłączać dopiero wraz z własnymi sagami.
2. **`SqlCommandDeliveryDispatcher` wymaga aktywnego `DeliverySessionScope`** (rzuca
   `RuntimeError` bez scope'a) — dispatch delivery jest możliwy **wyłącznie wewnątrz
   transakcji inbox**. To jawny wymóg projektowy (§5.2/§6.4: saga dispatchuje kroki
   tylko w handlerach przetwarzanych przez inbox), ale musi być rozpoznany, nie ukryty.
3. **`EventBus.publish` wywołuje subskrybentów sekwencyjnie w jednej transakcji** —
   błąd jednego subskrybenta → retry całego rekordu. Dla sagi współdzielącej event
   z innymi subskrybentami to sprzężenie retry: wymaga decyzji (izolacja subskrybentów
   albo świadome zaakceptowanie "1 rekord = 1 grupa zmian").
4. **Routing komend jest per BC.** Publisher wysyła pod
  `command.<target_service>.<command_name>`, a consumer wiąże
  `command.<target_service>.#`; po odebraniu zapisuje każdą dostarczoną komendę
  do własnego inboxu bez dodatkowego filtrowania.

### 2.2 Stan ścieżki komend delivery (punkt startowy migracji)

Weryfikacja kodu: tor komend delivery jest **spięty dla pilota projektu** — strona
odbioru i relay są wiredowane, a komendy produkuje warstwa `process/`. Marker `ProcessCommand`
(`platform/process/process_command/`) jest **behaviorless i nieużywany** — nie
dziedziczy po nim żadna komenda biznesowa. To znaczy:

- pilot ma sens produkcyjny: tabele `saga_instance`/`saga_timeout` powstają z platformowego
  szablonu (`PersistenceDeliveryModels.sagas`) w baseline `0001_*` — `create_service_tables`
  iteruje metadata serwisu, dokładnie jak outbox/inbox (bez osobowych migracji sag);
- marker `ProcessCommand` został usunięty razem z testem, który wymuszał jego istnienie;
- migracja nadała torowi delivery właściciela (warstwa procesu), dopięła relay
  producenta i zablokowała aplikację jako producenta dispatch delivery.

### 2.3 Dlaczego "po prostu kilka handlerów" nie wystarczy

Handlery aplikacyjne są **bezstanowe** i operują na **jednym agregacie** w jednej
transakcji (`pattern-standards/handler-structure`, `command-handler-structure`).
Saga jest **stanowa** i rozciąga się na wiele agregatów/BC — wymaga trwałości,
korelacji, kompensacji i timeoutu. To uzasadnia warstwę `process/` i trwałą
instancję sagi.

---

## 3. Model docelowy — jeden typ komendy, rola przez rejestrację

### 3.1 Słownik (zamiennik "sync/async")

| Pojęcie | Znaczenie |
|---|---|
| **Komenda lokalna** | komenda obsłużona i commitowana w **jednej transakcji** w usłudze, w której działa handler (`CommandBus → Handler → UoW → commit`). Niezależnie od tego, skąd przybyła (lokalne wywołanie albo delivery przez inbox). |
| **Komenda delivery** | komenda **rozproszona przez outbox→inbox** (at-least-once), obsłużona lokalnie w serwisie docelowym w osobnej transakcji. Wielotransakcyjność/i eventualność jest cechą transportu. |
| **Inicjalizator sagi** | komenda delivery, zarejestrowana w warstwie `process/` jako **start handler** — każde jej wystąpienie tworzy nową instancję sagi. |
| **Event** | fakt / rezultat / broadcast — `outbox_event` → `inbox_event`. |

Słowa "synchroniczna/asynchroniczna komenda" **nie używamy**: saga jest z natury
wielo-wydaniami (wiele transakcji), więc "synchronizm" byłby przegięciem.

### 3.2 Warstwa aplikacji

```
application/
├── commands/          # zwykłe komendy (jedyny typ: Command)
├── command_handlers/  # CommandHandler: UoW → agregat → commit
├── event_handlers/    # EventHandler: reakcja na fakty
└── queries/           # read side
```

- Komenda zarejestrowana w aplikacji = **komenda lokalna**: jedna transakcja.
- Handler aplikacyjny, który chce zlecić efekt **poza** swój serwis:
  - albo **publikuje event** (fakt) — gdy nie obchodzi go wykonawca;
  - albo **inicjuje sagę** (publikuje event startowy, na który reaguje start handler
    w `process/`) — gdy potrzebna jest koordynacja, kompensacja lub wynik.
- **Zakaz**: warstwa aplikacji nie dispatchuje komend przez tor delivery
  (reguła §7.1) — aplikacja nigdy nie woła `CommandDeliveryDispatcher`.

### 3.3 Warstwa procesu (saga)

```
process/<bc>/<nazwa_sagi>/
├── manager.py     # SagaManager — maszyna stanów
├── state.py       # SagaState (@dataclass) + SagaStatus (StrEnum)
├── handlers/      # stateless: start handler (inicjalizator) + event handlers (rezultaty)
├── ports/         # per-saga porty
└── steps.py       # tabela kroków: step → komenda + compensation + awaited_event
```

- **Jeden typ komendy** — różnica jest w rejestracji:
  - komenda typu `T` zarejestrowana jako start handler w `process/` = **inicjalizator
    sagi** (jej stabilny `command_name` wskazuje kontrakt, a `saga_type` proces, §5.3);
  - ta sama klasa `T` zarejestrowana z normalnym `CommandHandler` w aplikacji innego
    serwisu = zwykła komenda lokalna.
  - W jednym serwisie `CommandBus` mapuje typ → **jeden** handler i zgłasza błąd
    przy podwójnej rejestracji, więc rola danego typu jest jednoznaczna.
- **Kroki sagi** = komendy delivery dispatchowane przez proces do uczestników
  (te same klasy co zwykłe komendy; po stronie odbiorcy działają jak komenda lokalna).
- **Wyniki** = eventy; pilot obsługuje je lokalnie przez `EventBus`, a wariant
  rozproszony musi użyć `outbox_event` → `inbox_event`.

### 3.4 Role komunikatów (podsumowanie)

| Komunikat | Rola | Rejestracja / producent | Tor |
|---|---|---|---|
| Komenda (typ z app handlerem) | operacja lokalna | aplikacja (handler z UoW) | `CommandBus` (lokalnie) |
| Komenda (typ z start handlerem) | inicjalizator sagi | process (start handler) | delivery: `outbox_command` → `inbox_command` → start handler |
| Komenda (krok) | krok sagi / kompensacja | proces (SagaManager dispatch) | delivery: `outbox_command` → `inbox_command` → local handler |
| Event | fakt / rezultat / broadcast | każda warstwa | `outbox_event` → `inbox_event` |

---

## 4. Migracja funkcjonalności z aplikacji do procesu

### 4.1 Co dokładnie się zmienia

| Artefakt | Stan obecny | Stan docelowy |
|---|---|---|
| `ProcessCommand` (marker) | `platform/process/process_command/process_command.py`, nieużywany | **usunięty** (klasa + re-export + test architektury) |
| `CommandDeliveryDispatcher` (port) | `application/ports/command/command_delivery_dispatcher.py` | **`platform/process/saga/ports/command_delivery_dispatcher.py`** |
| Rola producenta komend delivery | "dostępna w aplikacji" | **wyłącznie proces** — aplikacja zablokowana testem |
| `outbox_command`/`inbox_command`, `CommandInboxProcessor`, rabbit consumer | transport delivery | **zostają** (mechanizm); pilot ma relay + `RabbitCommandDeliveryTransport` |
| Adaptery (`SqlCommandDeliveryDispatcher` itd.) | `infrastructure/messaging/command/` | zostają (adaptery w infrastrukturze) |

### 4.2 Kroki migracji

1. **Marker `ProcessCommand`** — usunięty; platforma używa jednego typu `Command`.
2. **Port `CommandDeliveryDispatcher`** — przeniesiony do
  `platform/process/saga/ports/`; import-linter pozostaje zielony.
3. **Reguła ścieżki dispatch** (re-anchor z typów na transport):
   - `test_application_does_not_dispatch_delivery_commands` — w `application/`
     (platform + BC) nie ma importu `CommandDeliveryDispatcher`,
     `SqlCommandDeliveryDispatcher`, `SqlCommandOutboxWriter` i nie ma wywołań
     `.dispatch(..., target_service=...)`;
   - `test_delivery_dispatch_only_from_process` — dispatch delivery występuje
     wyłącznie w `process/` (+ `infrastructure/` adapterach, `bootstrap` DI).
4. **Rejestracja ról w DI**: start handler sagi rejestrowany na `CommandBus`
   (`CommandBus.register(CommandType, saga_start_handler_factory)`); kontrakty
   komend delivery (kroki i inicjatory) w katalogu kontraktów BC (`CommandContract`).
5. **Uporządkuj nazewnictwo/wskazówki** w skillach: "komenda delivery" i
   "inicjalizator sagi" (rola przez rejestrację) — usuń pojęcie komendy "procesowej"/
   "asynchronicznej" jako zakresu prowizyjnego, bo w modelu docelowym NIE istnieje.
6. **Strona producencka pilota** — `CommandOutboxToTransportRelay`,
  `RabbitCommandDeliveryTransport` i worker są zarejestrowane w `project_service`.

### 4.3 Skutek migracji

- Aplikacja ma **jedną, jednolitą komendę** — brak drugiej typologii.
- Tor delivery jest **celowy**: działa wyłącznie jako nośnik komend saga (kroki) i
  inicjalizatorów; jego producentem jest proces.
- Rola jest **jawna w rejestracji** (`configure_*`, kontrakt w katalogu) — łatwa do
  audytu i testowana architektonicznie.

---

## 5. Architektura docelowa wsparcia sag

### 5.1 Topologia pakietów

```
shell/platform/process/                      # budulce warstwy procesu
└── saga/
    ├── base/
    │   ├── saga_manager.py                  # abstrakcyjna maszyna stanów (dziedziczona przez BC)
    │   └── saga_state.py                    # typy stanu: SagaStatus, SagaStep (wzorce)
    ├── correlation/
    │   ├── event_route.py                   # EventRoute(saga_type, extract_key, on_new_instance)
    │   └── saga_registry.py                 # rejestr: event/command -> routes; saga_type -> start handler/manager factory
    ├── ports/
    │   ├── command_delivery_dispatcher.py      # [MIGRATED] port dispatch komend delivery
    │   ├── saga_repository.py               # Protocol: load/save/get_by_key
    │   └── saga_timeout_repository.py       # Protocol: schedule/claim timeoutów
    └── steps.py                             # StepDefinition(step, command, compensation, awaited_by)

shell/platform/infrastructure/process/saga/  # adaptery (SQL)
├── models/saga_delivery.py                  # build_saga_delivery_models(base) → saga_instance + saga_timeout
├── repositories/sql_saga_repository.py      # SQLAlchemy (active session scope)
├── repositories/sql_saga_timeout_repository.py
└── worker/saga_timeout_processor.py         # subclass InboxProcessorBase
```

Sagi per BC (cel: `package-topology` + aktywne testy `test_process_structure__*`):

```
shell/<service>/process/<bc>/<saga>/
├── manager.py        # SagaManager — przejścia stanu
├── state.py          # SagaState @dataclass + SagaStatus StrEnum
├── handlers/         # stateless: start handler + event handlers (rezultaty)
├── ports/            # per-saga porty
└── steps.py          # tabela kroków sagi
```

### 5.2 Przepływ sagi

```
Komenda `X` (inicjalizator, handler = start handler w process/):
  outbox/inbox → CommandInboxProcessor → CommandBus → StartHandler(X)
     ├─ dedup (processed_delivery / unikalny (saga_type, saga_key))
    ├─ utworzenie instancji sagi (`saga_type` = stabilny identyfikator procesu)
     └─ dispatch kroku 1 (komenda delivery)   # at-least-once

Krok: dyspatch komendy delivery -> uczestnik -> local handler (commit)
       -> event rezultatu (outbox_event) -> saga: inbox_event -> SagaManager.on_event
       -> guard stanu -> następny krok / kompletacja / kompensacja
```

### 5.3 Rola "inicjalizatora" i `saga_type`

- `saga_type` jest stabilnym identyfikatorem procesu, niezależnym od
  `command_name` komendy-inicjalizatora. Przykład pilota: `project_provision` oraz
  `project.project_provision.start` to dwa różne identyfikatory o różnych rolach.
  `saga_type` nie jest osobnym typem komendy ani markerem.
- Instancja korelowana przez `(saga_type, saga_key)`; `saga_key` z payloadu
  inicjalizatora (klucz biznesowy, np. `order_id`) albo generowany `command_id`.
- `correlation_id` łączy outbox/inbox wszystkich kroków w tracing — nie jest kluczem
  korelacji sagi (może być wspólny dla kilku instancji).

### 5.4 Model danych

`build_saga_delivery_models(base)` (wzorzec: `build_event_delivery_models`).

**`saga_instance`** — stan sagi (per BC metadata):

| Kolumna | Typ | Znaczenie |
|---|---|---|
| `id` | str PK | `SagaId` |
| `saga_type` | str | stabilna nazwa procesu, niezależna od nazwy komendy |
| `saga_key` | str | biznesowy klucz korelacji (np. `order_id`) — jedna instancja na proces i klucz |
| `status` | str | `SagaStatus` (RUNNING / FAILING / COMPENSATING / COMPENSATED / COMPLETED) jako StrEnum |
| `current_step` | str nullable | krok, na który czekamy |
| `business_payload` | JSONB | stan biznesowy sagi (`SagaState` — `@dataclass(frozen=True)`) |
| `completed_steps` | JSONB default `[]` | wykonane kroki (kolejność kompensacji) |
| `failed_steps` | JSONB default `[]` | kroki zakończone błędem |
| `version` | int | optimistic locking (dwa eventy o tę samą instancję) |
| `created_at`/`updated_at`/`completed_at`/`failed_at`/`compensated_at` | timestamps | czas życia |

**`saga_timeout`** — timeout kroku jako rekord *przetwarzany jak rekord inbox*
(ten sam `InboxStateMixin`): `id`, `saga_id`, `saga_key`, `step`, `due_at` +
kolumny `InboxStateMixin` (status/lease/next_attempt/retry_count/error/...).
Dzięki temu timeout przechodzi przez `InboxClaimService` → `InboxProcessorBase`
(claim→retry→DLQ, lease, heartbeat, reclaim po awarii) **bez nowego procesora**.

> Zgodność z `model-migration-sync`: tabele `saga_instance`/`saga_timeout`
> budowane fabryką per BC + migracja Alembic w schemacie każdego serwisu.

---

## 6. Kluczowe elementy wsparcia

### 6.1 Maszyna stanów — `SagaManager`

```python
# shell/platform/process/saga/base/saga_manager.py
class SagaManager(ABC):
    def __init__(self, saga_id, saga_key, steps: StepRegistry,
                 dispatcher: CommandDeliveryDispatcher,
                 repository: SagaRepository,
                 timeouts: SagaTimeoutRepository) -> None: ...

    @abstractmethod
    async def on_event(self, event) -> None:
        """guard(stanie) → mutacja stanu → _execute_step dla następnych kroków."""

    async def dispatch_step(self, step, command) -> str:
      # zapis stanu kroku, dispatch i timeout odbywają się w jednej transakcji
      ...

    async def dispatch_compensation(self, step, command) -> str:
      ...
```

Zasady (skille `saga`, `saga-structure`):
- saga **nigdy nie implementuje logiki domenowej** — tylko koordynację;
- każda metoda zaczyna się **guardem stanu** (event/komenda nieaktualne → ignoruj);
- `SagaState` = `@dataclass(frozen=True)`, `SagaStatus` = `StrEnum`
  (wymóg `test_saga_state_is_dataclass`).

### 6.2 Start sagi — inicjalizator i rejestracja

Start przez **komendę inicjalizatora** (podstawowy):

```python
# bootstrap/<bc>/container/<bc>_core_container.py  (configure_*)
command_bus.register(OrderFulfillmentStartCommand, container.order_fulfillment_start_handler_factory)
```

Start handler (warstwa process):

```python
class OrderFulfillmentStartHandler(CommandHandler[OrderFulfillmentStartCommand]):
    def __init__(self, repository, manager_factory) -> None:
        ...

    async def handle(self, command) -> None:
      if await self._repository.get_by_key("order_fulfillment", command.order_id):
            return
      await self._manager_factory(command.order_id).start(command)
```

Alternatywnie start przez **event startowy**: `EventRoute(saga_type=..., extract_key=...,
on_new_instance=True)` + handler eventu tworzący instancję — analogiczny kształt.

### 6.3 Korelacja rezultatów — `SagaRegistry` / `EventRoute`

Saga dostaje eventy po deserializacji przez `EventInboxProcessor` → `EventBus`.
Pilot koreluje je przez `SagaRepository.get_by_key`; `SagaRegistry` jest obecnie
tylko fail-fast rejestrem tras i nie tworzy ani nie lokalizuje instancji:

```python
@dataclass(frozen=True, slots=True)
class EventRoute:
    saga_type: str
    extract_key: Callable[[IntegrationEvent], str]    # np. event.aggregate_id.value
    on_new_instance: bool = False
```

- **Start**: handler sprawdza istniejącą instancję i dopiero tworzy nową.
- **Kontynuacja**: handler pobiera instancję po `saga_key` i przekazuje jej `saga_id`
  do fabryki managera.
- Rejestr per BC (fail-fast, jak rejestr kontraktów komend — duplikat typu/trasy = błąd).

### 6.4 Atomowość — jedna transakcja na event sagi

Przetwarzanie rekordu inbox jest w transakcji processora
(`InboxProcessorBase._process_in_transaction`); handler dostaje
`DeliverySessionScope`. Saga zatem:
- aktualizuje `saga_instance` przez repo na `scope.session`;
- dispatchuje komendę delivery przez `CommandDeliveryDispatcher` → wiersz
  `outbox_command` na `scope.session` (`infrastructure/messaging/command/sql_command_outbox_writer.py:117`);
- **nie woła `commit()`** — processor robi ack + commit.

Efekt: `saga_instance.{status,current_step,business_payload}` +
`outbox_command.*` (kroki) + ack inbox = **jedna transakcja** (zakres: jeden BC).
Awaria → rollback wszystkich trzech → retry (idempotentny dzięki guardowi stanu +
`processed_delivery`).

> Saga w BC, który nie jest właścicielem stanu, to nie saga — to zwykły event
> handler (reguła `test_cross_aggregate_discipline__test_process_handlers_dont_use_cross_bc_repos`).

### 6.5 Kompensacje

1. Kompensacje kroków wykonanych są uruchamiane w odwrotnej kolejności.
2. Krok z `compensate_on_failure=True` może być kompensowany także po częściowym
  wykonaniu, jak `provision_workspace` w pilocie.
3. Zapis intencji kompensacji ustawia `COMPENSATING`; `COMPENSATED` pojawia się
  dopiero po evencie `WorkspaceReleased`.
4. Kompensacje muszą być idempotentne po stronie odbiorcy (inbox + guard).

### 6.6 Timeouty — reużycie machinerii inbox

Rejestracja: `dispatch_step` → `self._timeouts.schedule(...)`.
Odpalanie: `SagaTimeoutProcessor(InboxProcessorBase)` claimuje `saga_timeout`
z `due_at <= now` (lease), dispatches event `SagaTimedOut` na `EventBus`
(subskrybent: saga handler → `manager.on_timeout(step)`), ack w tej samej
transakcji. Sukces anuluje oczekujący timeout, a handler timeoutu sprawdza
`saga_id`, `current_step`, status i wersję przed kompensacją. Retry/backoff/DLQ/heartbeat/reclaim — **za darmo** z
`InboxProcessorBase`; worker przez `run_delivery_workers`.

### 6.7 Handler procesowy (kształt — stateless)

```python
# process/<bc>/<saga>/handlers/payment_completed_handler.py
class PaymentCompletedSagaHandler(EventHandler[PaymentCompletedIntegrationEvent]):
    def __init__(self, repository, manager_factory) -> None:
      self._repository = repository
        self._manager_factory = manager_factory

    async def handle(self, event) -> None:
      instance = await self._repository.get_by_key("order_fulfillment", event.order_id)
      if instance is not None:
        await self._manager_factory(event.order_id, saga_id=instance.saga_id).on_event(event)
```

Stateless + konstruktorowa injekcja (spełnia aktywne testy
`test_process_structure__test_process_handlers_*`).

### 6.8 Observability

- **Tracing**: `correlation_id`/`causation_id` z inbox do outbox; `SagaId` jako
  dodatkowy atrybut logowania.
- **Metryki** (port `MetricsBackend`): `saga_started_total`,
  `saga_completed_total`, `saga_failed_total`, `saga_compensated_total`,
  `saga_timeout_total`, `saga_duration_seconds`.
- **Readiness**: backlog `saga_timeout` (jak `SqlReadinessProbe`).

### 6.9 DI / Composition Root (per BC)

```python
# bootstrap/<bc>/container/<bc>_core_container.py
saga_repository = providers.Singleton(SqlSagaRepository, models=...)
saga_timeout_repository = providers.Singleton(
  SqlSagaTimeoutRepository, models=..., source_service="..."
)
command_delivery_dispatcher = providers.Singleton(
  build_command_delivery_dispatcher,
  commands=BC_COMMAND_CONTRACTS,
  models=...,
  source_service="...",
)
saga_timeout_processor_factory = providers.Factory(
    SagaTimeoutProcessor, session_factory=session_factory, event_bus=event_bus,
    models=saga_delivery_models, ... like event_inbox_processor_factory,
)
order_fulfillment_manager_factory = providers.Singleton(
    OrderFulfillmentSagaManager, repository=saga_repository,
    dispatcher=command_delivery_dispatcher, timeouts=saga_timeout_repository, ...)

# configure_<bc>(container): rejestracja ról
command_bus.register(OrderFulfillmentStartCommand, container.order_fulfillment_start_handler_factory)
event_bus.subscribe(PaymentCompletedIntegrationEvent, container.payment_completed_saga_handler_factory)
```
Kompensacje idempotentne: kontrakty komend delivery (kroki i inicjatory) w katalogu
komend BC (`CommandContract`) — inaczej dispatcher rzuca
`ValueError: No command contract for ...`.

---

## 7. Testy

### 7.1 Reguły architektury — granica aplikacja↔proces (nowe)

- `test_application_does_not_dispatch_delivery_commands` — **core reguły**: w
  `application/` (platform + BC) brak importów `CommandDeliveryDispatcher` /
  `SqlCommandDeliveryDispatcher` / `SqlCommandOutboxWriter` i brak
  `.dispatch(..., target_service=)`.
- `test_delivery_dispatch_only_from_process` — dispatch delivery w `process/`
  (+ `infrastructure/` adaptery, `bootstrap` DI) — nie w aplikacji.
- Usunięcie testu markera: `test_process_structure__test_process_command_extends_command_and_is_behaviorless.py`
  (nie ma już osobnego typu `ProcessCommand`).
- Migracja portu: aktualizacja `test_application_port_topology.py` oraz
  `test_application_structure__test_command_ports_are_typed_on_command.py`
  (ścieżka `CommandDeliveryDispatcher` → `platform/process/saga/ports/`).

### 7.2 Testy architektury — istniejące, aktywne dla `process/`

- `test_process_structure__test_process_handlers_are_stateless.py`
- `test_process_structure__test_process_handlers_have_async_handle.py`
- `test_process_structure__test_process_handlers_have_single_handle_method.py`
- `test_process_structure__test_process_handlers_dont_mutate_aggregates.py`
- `test_process_structure__test_saga_state_is_dataclass.py`
- `test_cross_aggregate_discipline__test_process_handlers_dont_use_cross_bc_repos.py`
- `test_imports__test_process_layer_imports.py` (process nie importuje
  infra/framework/bootstrap/sqlalchemy/fastapi)

Uwaga: reguły aplikacji (np. "application nie importuje ORM") obejmą także
`platform/process/` — utrzymać zgodność (process importuje `domain`/`application`).

### 7.3 Testy jednostkowe

`shell/tests/<bc>/unit/process/`:
- przejścia stanu z `InMemorySagaRepository` + `FakeCommandDeliveryDispatcher`;
- guardy: event/komenda poza stanem ignorowany;
- start: dedup inicjalizatora (jedna instancja per delivery);
- `_compensate()` w odwrotnej kolejności;
- rejestracja i anulowanie timeoutów przy `dispatch_step`;
- contract lookup dla komend delivery (fail-fast bez kontraktu).

Pilot projektu ma dodatkowo test wiring’u kontenera w
`shell/tests/project_service/unit/bootstrap/test_project_container_saga_wiring.py`
oraz test przepływu `ProjectProvisionSaga` w
`shell/tests/project_service/unit/process/test_project_provision_saga.py`.

### 7.4 Testy integracyjne (SQLite)

`shell/tests/<bc>/integration/sql_sqlite/`:
- pełny flow saga: inicjalizator → instancja → `outbox_command` (krok) → local
  handler → event rezultatu → następny krok → kompletacja;
- retry/DLQ timeoutu (`saga_timeout` z opóźnieniem `due_at`);
- odzyskiwanie po "restart" (instancja wczytana z bazy).

Ostateczna wyrocznia: `run_tests.ps1` bez błędów (`run-tests-validator`).

---

## 8. Plan wdrożenia (etapy)

Legenda: `[x]` — wykonane i zwalidowane, `[ ]` — do wykonania.

**Etap 0 — uporządkowanie typologii + szkielet platformy**
- [x] Usunięcie markera `ProcessCommand` (moduł, re-export, test architektury, grep importów).
- [x] Przeniesienie portu `CommandDeliveryDispatcher` → `platform/process/saga/ports/`
      (aktualizacja topologii/2 testów + import-linter).
- [x] Reguły ścieżki dispatch (§7.1): aplikacja nie używa toru delivery; tylko `process/`.
- [x] Puste klasy bazowe saga, `SagaRegistry`, `EventRoute`, `steps`, `SagaInstance`,
      `SagaTimedOut` w `platform/process/saga/`.
- [x] Modele `saga_instance`/`saga_timeout` + fabryka `build_saga_delivery_models`
      (`platform/infrastructure/process/saga/`) + **wpięte do platformowego bundla
      `PersistenceDeliveryModels.sagas`** (każdy BC otrzymuje te tabele w swoim
      metadata przez `build_persistence_delivery_models`) + `SqlSagaRepository`
      (jawne `create`/`update` + optimistic locking) + `InMemorySagaRepository`
      + testy (unit + SQLite).
- [x] **Refaktoryzacja §2.1b**: `CommandOutboxToTransportRelay` +
  `RabbitCommandDeliveryTransport` są podłączone dla `project_service`;
  pilot ma provider relaya i worker command outbox. Izolacja subskrybentów
  `EventBus` (§2.1b.3) pozostaje otwarta.
- [x] Migracje `saga_instance`/`saga_timeout` — wzorzec „jak z outboxami": platformowy
  szablon (`build_saga_delivery_models` w `PersistenceDeliveryModels.sagas`), każdy serwis
  buduje je z platformy. Tabele powstają w `0001_*_baseline` (`create_service_tables` iteruje
  metadata) — bez osobnych migracji sag.

**Etap 1 — state machine + persistence**
- [x] `SagaManager` (ABC) z `dispatch_step` (timeout przy starcie kroku) i
      `dispatch_compensation` (odwrotna kolejność kroków w __compensation__).
- [x] `SagaRepository` (SQL + InMemory — optimistic locking, testy SQLite/unit).
- [x] `SagaTimeoutProcessor` (claim per `next_attempt_at = due_at`) +
      `SqlSagaTimeoutRepository` + testy (firing, nie-claim przyszłych, retry→DLQ).
- [x] Adapter portu `CommandDeliveryDispatcher` (`build_command_delivery_dispatcher`)
      + test SQLite (wiersz `outbox_command`, błąd braku kontraktu).
- [x] **Pilot**: `ProjectProvisionSaga` w `shell/project_service/process/project/project_provision/`
      (inicjalizator `StartProjectProvisionCommand` → instancja → krok
      `ProvisionWorkspaceCommand` przez `outbox_command` → handler → event rezultatu
      → kompletacja; porażka → kompensacja `ReleaseWorkspaceCommand`). Transport
      w teście symulowany (klon `outbox_command`→`inbox_command`); pełny szlak
      relay+broker wymaga Rabbit (§2.1b). Nowe komendy/eventy dołączone do
      manifestu kontraktów komend BC; reguły process/application spełnione. Test używa
      transportu symulowanego, natomiast production wiring jest w `project_service`.

**Etap 2 — kompensacje + timeouty + observability**
- [x] Pilot obsługuje kompensację z cyklem
  `RUNNING→COMPENSATING→COMPENSATED`, potwierdzeniem eventu i guardami stanu.
  Ogólny mechanizm wielokrokowej kompensacji pozostaje do rozszerzenia.
- [x] `saga_timeout` + `SagaTimeoutProcessor` — worker uruchamiany przez
      `run_delivery_workers(extra_processors=...)` bez konsumenta brokera;
      zakablowany w `project_service` (kontener provider + main) jako referencja.
- [ ] Metryki (`saga_started_total`...) i readiness backlogu timeoutów.

**Etap 3 — dojrzałość**
> brokera. Obsługa błędu technicznego po wyczerpaniu retry/DLQ oraz metryki/readiness
> nadal wymagają osobnych kontraktów i testów.

**Etap 3 — dojrzałość**
- Readiness backlog timeoutów, upcasting payloadów sagi, read-side
  `saga_instance`, replay/retention (wzorce z inbox).

---

## 9. Decyzje i luki do domknięcia

### 9.1 Decyzje do potwierdzenia

1. **Usunięcie markera `ProcessCommand`** — przyjęte; istnieje jeden typ `Command`.
2. **Start sagi** — pilot używa komendy inicjalizatora zarejestrowanej w `process/`.
  Start przez event pozostaje możliwym rozszerzeniem.
3. **Krok intra-service** — pilot używa komendy delivery, aby zachować trwałą
  intencję i osobną transakcję kroku.
4. **Timeouty** — pilot używa `saga_timeout` + `InboxProcessorBase`.
5. **Granularność kroków** — jeden krok produkuje jedną komendę.
6. **Migracje** — tabele sagi tworzone przez `0001_*_baseline` (metadata `create_service_tables`);
   brak osobnych migracji sag (wzorzec „jak z outboxami").

### 9.2 Zrealizowane kontrakty i pozostałe luki

Pilot domyka kontrakty potrzebne do jednego przepływu lokalnego. Poniższe
ograniczenia są nadal jawne i nie mogą być przedstawiane jako gotowe wsparcie
każdej sagi.

#### Zrealizowane w pilocie

- `CommandDeliveryDispatcher`, repozytorium sagi i handlery używają `async`/`await`.
- Stan aktywnego kroku jest zapisywany przed dispatch; outbox komendy, stan i ack
  inboxu są commitowane atomowo w zakresie jednego BC.
- Start jest deduplikowany po `(saga_type, saga_key)`, a zapis chroni optimistic
  lockingiem po `version`.
- Sukces anuluje oczekujący timeout; timeout i rezultat sprawdzają `saga_id`,
  status oraz `current_step`.
- Kompensacja przechodzi przez `COMPENSATING` i dopiero po evencie potwierdzenia
  ustawia `COMPENSATED`.

#### Pozostało do wykonania

- Techniczna porażka delivery po DLQ nie wysyła jeszcze automatycznego eventu do
  sagi; bez osobnego kontraktu saga może pozostać w oczekiwaniu.
- Ogólny `SagaRegistry` nadal jest tylko rejestrem tras; pilot używa bezpośredniego
  lookupu w `SagaRepository`.
- Wielokrokowa kompensacja, retry kompensacji, częściowa porażka i wznowienie po
  DLQ wymagają osobnych testów systemowych.
- `saga_type` i `saga_key` mają politykę jednej instancji na całe życie pary.
  Ponowne uruchomienie po `COMPLETED`/`COMPENSATED` wymaga nowego klucza albo
  jawnego mechanizmu resetu; nie jest obecnie wspierane.
- Pełny przepływ przez RabbitMQ, metryki, readiness, read-side i retention są
  poza zakresem zaimplementowanego pilota.

---

## 10. Podsumowanie

Platforma ma wspólny transport, atomowość i warstwę `process/`. Pilot
`ProjectProvisionSaga` jest podłączony w `project_service`: ma stabilne kontrakty
komend, deduplikację startu, trwały stan, guardy, timeout i potwierdzoną
kompensację. Model nadal zachowuje **jeden typ komendy**, a rola wynika z
rejestracji (aplikacja = komenda lokalna; proces = inicjalizator i kroki delivery).
Nie jest to jeszcze pełne wsparcie wszystkich sag: DLQ techniczny, wielokrokowa
kompensacja, metryki, readiness, read-side i pełny test RabbitMQ pozostają
zadaniami roadmapy.