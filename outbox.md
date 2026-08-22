# Plan: jeden uniwersalny outbox/inbox z `kind` — wersja enterprise

Status: plan wdrożenia (akceptacja wymagań)
Data: 2026-08-22
Zakres: SHELL platforma + wszystkie Bounded Context (BC) — definition, execution, ingestion, project, scheduling, session, user.

---

## 1. Cel

Zbudować w platformie SHELL **jeden, uniwersalny, transakcyjny mechanizm dostarczania wiadomości** (outbox → relay → broker → inbox → processor), który obsługuje **wszystkie trzy typy komunikacji** — Command (intencja), Event (fakt), Message (dane) — przy użyciu **jednej pary tabel** (`outbox` / `inbox`) rozróżnianych kolumną `kind`, zamiast obecnych trzech par tabel delivery per BC.

Cele szczegółowe:

1. **Zero utraty i zero duplikatów** każdego deliverable — atomowy zapis ze stanem domeny (transactional outbox) dla **wszystkich** typów, nie tylko eventów.
2. **Minimalizacja złożoności operacyjnej** — 1 model, 1 publisher, 1 relay, 1 processor zamiast 3 zestawów maszynerii.
3. **Pełna identyfikowalność** (correlation/causation) i ślad audytowy dla każdego typu.
4. **Brak martwego kodu i brak miejsca na legacy/hacki** — każde rozwiązanie wymuszone typem i ograniczeniami bazy, nie umową programistyczną.
5. **Zgodność z praktyką enterprise** (NServiceBus, MassTransit, Debezium outbox): jedna tabela + `kind`, routing i kontrakty zróżnicowane na wyższych warstwach.

Semantyczna separacja Command/Event/Message **zostaje zachowana konceptualnie** — w kontraktach, registry, serializerach, deserializerach i busach (zgodnie z `skills/architectural-discipline/{command,event,message}-semantics`). Zmienia się wyłącznie warstwa fizycznej persystencji i dostarczania.

---

## 2. Problemy (obecny stan i to, co rozwiązujemy)

### 2.1. Stan obecny

Trzy pary tabel per BC:

```text
outbox_event   / inbox_event      (eventy)
outbox_message / inbox_message    (message)
outbox_command / inbox_command    (command)
```

Plus osobne maszyny: 3 procesory inbox (`EventInboxProcessor`, `MessageInboxProcessor`, `CommandInboxProcessor`), 2 autonomiczne publisherowie (`SqlMessageOutboxPublisher`, `SqlCommandOutboxPublisher`), 1 relay.

### 2.2. Defekty, które naprawiamy

| # | Problem | Dowód w kodzie | Konsekwencja |
|---|---|---|---|
| P1 | **Dual-write dla message/command** — zapis outboxa w osobnej sesji, poza transakcją domeny | `sql_message_outbox_publisher.py:50` (`async with self._session_factory()`) | Wiadomość może zginąć między commitem domeny a zapisem outboxa — ta sama klasa błędu, którą transactional outbox ma eliminować |
| P2 | **Martwy `stage_messages`** — buforowany, nigdy nie zapisywany | `sql_alchemy_uow_base.py:110` (stages) vs `_write_staged_outbox()` pisze tylko `_staged_events` | Protokół zapowiada funkcję, która nie działa |
| P3 | **Brak `stage_commands` w UoW** | `unit_of_work.py:16` tylko `stage_events`/`stage_messages` | Komendy nie mogą być transakcyjne; wymuszona nieatomowa ścieżka |
| P4 | **Nieużywane w produkcji** — tabele message/command żyją tylko w testach | `SqlMessageOutboxPublisher` tylko w `tests/` | 4 zbędne tabele per BC + maszyneria bez producenta/konsumenta |
| P5 | **3× maszyneria bez 3× polityki** | 6 tabel, 3 procesory, lease/heartbeat/dedup per typ | Koszt utrzymania bez odrębnej polityki retry/DLQ/retention |
| P6 | **Gołe stringi zamiast egzekwowanych typów** | `event_delivery.py` itd. — kolumny `str` bez CHECK | Literówka w `kind`/typie = cichy truciciel, który pada dopiero na deserializacji (DLQ) |
| P7 | **Audyt tylko eventów** | `sql_alchemy_uow_base.py:187` — `self._models.audit(...)` tylko w pętli eventów | Brak pełnego śladu dostarczania message/command |
| P8 | **Routing nieegzekwowany** — konsumenci wiążą goły `#` | `rabbit_inbox_consumer.py:65` (`routing_keys or ["#"]`) | „Łap wszystko" zamiast świadomego wyboru rodzajów |
| P9 | **Ciche zgubienie publikacji** | `rabbit_delivery_transport.py:58` (`mandatory=False`) | Nieroutowalna wiadomość znika cicho, gdy brak wiążącej kolejki |
| P10 | **Brak polityk per kind i metryk per kind** | globalne `max_retries`/backoff w `InboxProcessorBase` | Brak możliwości różnicowania i obserwacji per typ |

### 2.3. Co NIE jest problemem

Separacja semantyczna Command/Event/Message jako taka — jest poprawna i zostaje. Nie konsolidujemy kontraktów, registry ani deserializerów; konsolidujemy tylko tabele i maszynerię dostarczania.

---

## 3. Metody

Metody, które stosujemy do osiągnięcia celu:

| Metoda | Opis | Gdzie egzekwowana |
|---|---|---|
| **Transactional Outbox** | Deliverable zapisywane atomowo ze stanem domeny; relay publikuje po `published_at IS NULL`; `published_at` ustawiane dopiero po potwierdzeniu transportu | `SqlAlchemyUnitOfWorkBase._write_staged_outbox()` + `OutboxToTransportRelay` |
| **Inbox + lease/claim/retry/DLQ** | Dwie transakcje (claim z lease, ack warunkowy kluczowany `id+claimed_by`), retry z backoff, DLQ po `max_retries` | `InboxProcessorBase` + `InboxClaimService` |
| **Jedna tabela + `kind` (Debezium/NServiceBus)** | Pojedyncza tabela `outbox`/`inbox` z kolumną `kind`; kontrakty i routing różnicowane wyżej | `delivery.py` (nowy model) |
| **Typed constraints zamiast umów** | `DeliveryKind(StrEnum)` + `CheckConstraint` na `kind` i `contract_type` (NOT NULL, długość > 0) | model ORM + testy architektury |
| **Jeden punkt zapisu (UoW)** | 100% publikacji przez `stage_events`/`stage_messages`/`stage_commands` → atomowy zapis w UoW; zero publisherów z osobną sesją | port `UnitOfWork` + `SqlAlchemyUnitOfWorkBase` |
| **Routing po kind** | Topic `shell.delivery`, routing key `{kind}.{contract_type}`; kolejki wiążą jawne wzorce (`event.#` itd.), nigdy goły `#` | `RabbitDeliveryTransport` + konfiguracja konsumentów |
| **At-least-once + idempotencja** | Dedup insertu (`uq_inbox_outbox_id`, `ON CONFLICT DO NOTHING`) + dedup wykonania (`processed_delivery(consumer_name, outbox_id)`) | `RabbitInboxConsumer`, `ProcessedDeliveryStore` |
| **Zamrożony kontrakt wire** | `EnvelopeCodec` bez zmian; nieznany `kind` = nack + alert; zmiany tylko przez `wire_version` z upcasterem | test kontraktu w CI |
| **Polityki per kind + monitoring** | `Mapping[DeliveryKind, DeliveryPolicy]` + metryki claimed/processed/retried/dead_lettered/lag per kind | `DeliveryInboxProcessor`, metryki, alerty |

---

## 4. Uzasadnienie (dlaczego tak, a nie inaczej)

1. **Zgodność z praktyką branżową.** Pojedyncza tabela outbox/inbox + `kind` to dominujący wzorzec w production-grade systemach (NServiceBus, MassTransit, Debezium+CDC). Rozdział per typ jest tam dokonywany na poziomie kontraktu/routingu, nie schematu. Trzy osobne pary tabel to wariant rzadki i kosztowny, dopóki nie istnieją odrębne polityki.
2. **Eliminacja klasy błędu, a nie symptomu.** Osobna sesja w `SqlMessageOutboxPublisher`/`SqlCommandOutboxPublisher` reintrodukuje dual-write. Skoro mamy UoW i transactional outbox dla eventów — rozciągamy tę samą gwarancję na message i command (`stage_messages`/`stage_commands`), zamiast utrzymywać drugą, gorszą ścieżkę.
3. **Błąd nie może być cichy.** Literówka `kind`/pusty `contract_type` musi być odrzucona przez bazę/typ, zanim cokolwiek trafi do transportu — inaczej ciche DLQ dla całej klasy błędów. To eliminuje P6/P8/P9 twardo, nie „dobrymi intencjami".
4. **Mniej rzeczy do utrzymania.** 7 BC × 8 tabel delivery → 7 BC × (outbox + inbox + audit + dedup + heartbeat). Jeden processor/relay/publisher zamiast trzech. Mniej workerów, migracji, metryk, dokumentacji.
5. **Pełny audyt i identyfikowalność.** Wszystkie trzy typy dostają ślad (audyt + correlation/causation), nie tylko eventy.
6. **Zero martwego kodu.** Protokół UoW (`stage_messages`, nowe `stage_commands`) wykonuje to, co deklaruje. Usuwamy publisherowie, których nikt nie używa w produkcji.
7. **Kompatybilność bez ceny.** Wire format zamrożony (v1) — broker i istniejące bindingi działają; zmiany formatu są świadomym, wersjonowanym krokiem.
8. **Dlaczego NIE osobne tabele na przyszłość?** Bo gdy (i jeśli) polityki per kind będą realnie różne, `kind` w tabeli umożliwia filtrowanie bez zmiany schematu — a konsolidacja jest teraz tańsza niż później (migracja 6→2 jednorazowa, odwrotna byłaby rozrostem).

---

## 5. Docelowy model danych (odniesienie dla planu)

### 5.1. `DeliveryKind`

`shell/platform/domain/value_objects/delivery_kind.py`:

```python
class DeliveryKind(StrEnum):
    EVENT = "event"
    MESSAGE = "message"
    COMMAND = "command"
```

### 5.2. Tabela `outbox` (zamiast 3)

```text
id                 str PK
kind               str  NOT NULL  CheckConstraint(kind IN ('event','message','command'))
contract_type      str  NOT NULL  CheckConstraint(length(contract_type) > 0)
event_id           str  NULL      -- tylko kind='event'
source_service     str  NULL      -- tylko kind='event'
occurred_at        datetime(tz) NOT NULL
aggregate_id       str  NULL      -- tylko kind='event'
aggregate_name     str  NULL      -- tylko kind='event'
schema_version     int  NOT NULL DEFAULT 1            CheckConstraint(schema_version >= 1)
payload            JSONB NOT NULL DEFAULT '{}'
correlation_id     str  NOT NULL DEFAULT ''
causation_id       str  NOT NULL DEFAULT ''
published_at       datetime(tz) NULL

Indeksy: ix_outbox_published_at (published_at); ix_outbox_kind_published_at (kind, published_at)
```

### 5.3. Tabela `inbox` (zamiast 3)

Kolumny `InboxStateMixin` (status, next_attempt_at, lease_until, claimed_by, processed_at, failed_at, last_attempted_at, retry_count, error, error_code, error_message, schema_version) + nośnik:

```text
id                 str PK             kind, contract_type — jak w outbox
outbox_id          str  NOT NULL
occurred_at, payload, correlation_id, causation_id, received_at
event_id/source_service/aggregate_id/aggregate_name  NULL (tylko event)

Więzy: UniqueConstraint("outbox_id", name="uq_inbox_outbox_id")
Indeksy: ix_inbox_status_next_attempt_received, ix_inbox_status_lease_until, ix_inbox_kind
```

### 5.4. Otoczenie

`audit_event` (payload wzbogacony o `kind` i `contract_type`), `processed_delivery`, `worker_heartbeat` — bez zmian schematu.

### 5.5. Kompatybilność wire (broker)

`EnvelopeCodec` bez zmian: `kind`, `outbox_id`, `{kind}_type`, `occurred_at`, `schema_version`, `payload`, `correlation_id`, `causation_id` (+ metadane eventu). `decode` waliduje `kind` przez `DeliveryKind` (nieznany → nack + alert). Zmiany formatu tylko przez `wire_version` + upcaster; zakaz aliasów/podwójnych kluczy.

---

## 6. Plan zmian — punkt po punkcie (z weryfikacją każdego kroku)

Każdy krok ma: **Zmianę** (co → na co), **Jak** (jak zrealizować), **Weryfikację** (jak potwierdzić poprawność).

### Krok 1 — `DeliveryKind` (nowy typ domenowy)

- **Zmiana**: brak → nowy plik `shell/platform/domain/value_objects/delivery_kind.py` z `DeliveryKind(StrEnum)` (EVENT/MESSAGE/COMMAND).
- **Jak**: dodać klasę; `StrEnum` z `"event"`, `"message"`, `"command"` (zgodnie z `constant-and-enum-naming-standards`).
- **Weryfikacja**: test `test_delivery_kind.py` (wartości enum); `mypy` przechodzi.

### Krok 2 — uniwersalne modele ORM `delivery.py`

- **Zmiana**: nowy `shell/platform/infrastructure/persistence/sql/models/delivery.py` z `build_delivery_models(base) -> DeliveryModels` (NamedTuple `outbox`/`inbox`); do usunięcia `event_delivery.py`, `message_delivery.py`, `command_delivery.py`.
- **Jak**: zbudować `OutboxModel` (tabela `outbox`) i `InboxModel` (tabela `inbox`, `InboxStateMixin`) wg sekcji 5: kolumna `kind` + `contract_type` + nullable metadane eventu; `CheckConstraint` na `kind`/`contract_type`/`schema_version`; indeksy i `uq_inbox_outbox_id`; nazwy klas `f"{base.__name__}OutboxModel"` / `...InboxModel`.
- **Weryfikacja**: test, że `metadata.tables == {"inbox","outbox"}`; INSERT z niepoprawnym `kind` lub pustym `contract_type` zwraca `IntegrityError`.

### Krok 3 — restrukturyzacja `PersistenceDeliveryModels`

- **Zmiana**: w `shell/platform/infrastructure/persistence/sql/models/persistence_delivery.py` pola `events`/`messages`/`commands` → jedno `delivery: DeliveryModels` (audit/processed_delivery/worker_heartbeat bez zmian).
- **Jak**: podmienić `NamedTuple` i `build_persistence_delivery_models`; `build_delivery_models(base)` zamiast trzech buildów.
- **Weryfikacja**: `rg "models\.events|models\.messages|models\.commands"` → 0 wpisów; testy metadata (sekcja 7) przechodzą.

### Krok 4 — `stage_commands` w porcie i implementacjach memory

- **Zmiana**: port `shell/platform/application/ports/persistence/unit_of_work.py` (obecnie `stage_events` + `stage_messages`) → + `stage_commands(commands: Sequence[object])`; implementacje memory (definition/session/scheduling/execution `unit_of_work.py`) analogicznie.
- **Jak**: dodać metodę do protokołu i buforów; zsynchronizować nazwy (zakaz skrótów per `variable-naming-standards`).
- **Weryfikacja**: `mypy` — brak „not implemented"; test protokołu `UnitOfWork` wymusza obecność wszystkich trzech metod.

### Krok 5 — UoW pisze eventy, message i komendy atomowo + audyt wszystkich kindów

- **Zmiana**: `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py` — `_write_staged_outbox()` obecnie pisze tylko `_staged_events` (i audyt tylko eventów) → pisze `_staged_events` (kind=EVENT), `_staged_messages` (kind=MESSAGE), `_staged_commands` (kind=COMMAND) do `models.delivery.outbox` oraz audyt dla każdego deliverable (payload + `kind` + `contract_type`).
- **Jak**:
  - `_staged_messages` → `contract_type=type(message).__name__`, `occurred_at=message.occurred_at`, payload przez `DomainMessageSerializer` (**w tej samej transakcji**, bez osobnej sesji);
  - `_staged_commands` → `contract_type=type(command).__name__`, payload serializowany na podstawie kontraktu komendy;
  - metadane eventu (`event_id`, `source_service`, `aggregate_id`, `aggregate_name`) tylko dla EVENT;
  - audyt rozszerzony na wszystkie trzy rodzaje.
- **Weryfikacja**: test transakcyjny — po `commit` wiersze wszystkich kindów są w `outbox`; po `rollback` **zero** wierszy (brak dual-write); `stage_messages`/`stage_commands` przestają być martwe.

### Krok 6 — `SqlDeliveryOutboxPublisher` (jeden punkt zapisu) + usunięcie starych publisherów

- **Zmiana**: nowy `shell/platform/infrastructure/messaging/delivery/sql_delivery_outbox_publisher.py` operujący **wyłącznie przez UoW** (stage, nie zapis w osobnej sesji); usunąć `sql_message_outbox_publisher.py`, `sql_command_outbox_publisher.py`, testowe `InMemoryMessageOutboxStore`, `FakeMessagePublisher`.
- **Jak**:

```python
async def stage_delivery(
    self, uow: UnitOfWork,
    kind: DeliveryKind,
    contract_type: str,
    payload: dict[str, object],
    occurred_at: datetime,
    *,
    event_id: str | None = None,
    source_service: str | None = None,
    aggregate_id: str | None = None,
    aggregate_name: str | None = None,
    schema_version: int = 1,
) -> None
```

  delektuje do `uow.stage_events` / `uow.stage_messages` / `uow.stage_commands` wg `kind`. Brak jakiejkolwiek ścieżki „osobna sesja".
- **Weryfikacja**: test architektury zakazujący importu starych módów + test, że `SqlDeliveryOutboxPublisher` nie tworzy sesji (nie trzyma `session_factory`); `rg "session_factory"` w nowym publisher = 0.

### Krok 7 — uniwersalny `OutboxToTransportRelay`

- **Zmiana**: `shell/platform/infrastructure/messaging/transport/outbox_to_transport_relay.py` — `models: EventDeliveryModels | MessageDeliveryModels | CommandDeliveryModels` + `kind: DeliveryKind` → `models: DeliveryModels` + opcjonalny filtr `kind: DeliveryKind | None = None`; `_to_envelope` czyta `{kind}_type` → `contract_type` z wiersza.
- **Jak**: selekcja `WHERE published_at IS NULL` (+ `AND kind = :kind` gdy filtr), `ORDER BY occurred_at`, `FOR UPDATE SKIP LOCKED`; `_to_envelope`: `kind=DeliveryKind(row.kind)`, `contract_type=row.contract_type`, metadane eventu `getattr(row, "event_id", None)`; protokoły `DeliveryOutboxModel`/`DeliveryOutboxRow` + pola `kind`/`contract_type`.
- **Weryfikacja**: test `test_outbox_to_transport_relay.py` (warianty event/message/command) — relay publikuje poprawne `DeliveryEnvelope` dla każdego `kind` i ustawia `published_at` wyłącznie po sukcesie.

### Krok 8 — `mandatory=True` w `RabbitDeliveryTransport`

- **Zmiana**: `shell/platform/infrastructure/messaging/transport/rabbit/rabbit_delivery_transport.py:58` `mandatory=False` → `mandatory=True` (default).
- **Jak**: zmienić argument `exchange.publish(..., mandatory=True)`; nieroutowalna wiadomość (brak wiążącej kolejki) = zwrot → `deliver()` zgłasza błąd → relay traktuje jako porażkę (retry/DLQ).
- **Weryfikacja**: test jednostkowy transportu z publi sher confirms — wiadomość bez wiążącego binding zgłasza błąd; `rg "mandatory=False"` → 0.

### Krok 9 — walidacja `kind` w `EnvelopeCodec.decode`

- **Zmiana**: `shell/platform/infrastructure/messaging/transport/envelope_codec.py` — sprawdzenie `kind not in ("event","message","command")` → walidacja przez `DeliveryKind`.
- **Jak**: `DeliveryKind(raw_kind)` w try/catch — nieznany `kind` = `ValueError` (obecny kontrakt rzuca, ale na gołych stringach); bez zmiany formatu wire.
- **Weryfikacja**: `test_envelope_codec.py` — nieznany `kind` rzuca; wire v1 nadal dekodowany identycznie.

### Krok 10 — uniwersalny `RabbitInboxConsumer`

- **Zmiana**: `shell/platform/infrastructure/messaging/transport/rabbit/rabbit_inbox_consumer.py` — `models: DeliveryModels`; `_persist` zapisuje `kind` i `contract_type` (zamiast kolumny `{kind}_type`); metadane eventu warunkowo dla `kind == "event"`; binding z **jawnymi** wzorcami (`event.#`, `message.#`, `command.#`) — zakaz gołego `#`.
- **Jak**: `values = {"kind": envelope.kind, "contract_type": envelope.contract_type, ...}`; `ON CONFLICT DO NOTHING` na `uq_inbox_outbox_id`; w konfiguracji kolejki jawnie podać wzorce routingu.
- **Weryfikacja**: test `test_rabbit_inbox_consumer` (jeśli istnieje) lub test unitu konsumenta — wiersz zapisany z `kind`/`contract_type`; duplikat `outbox_id` nie tworzy drugiego wiersza.

### Krok 11 — `DeliveryPolicy` (kontrakt polityki per kind)

- **Zmiana**: nowy `shell/platform/infrastructure/messaging/delivery/delivery_policy.py` — frozen dataclass `DeliveryPolicy`.
- **Jak**:

```python
@dataclass(frozen=True)
class DeliveryPolicy:
    max_retries: int = 3
    retry_backoff_seconds: int = 30
    max_retry_backoff_seconds: int = 3600
    retry_jitter_seconds: float = 0.0
    lease_duration_seconds: int = 60
    retention_days: int = 30
```

- **Weryfikacja**: test walidacji (wartości > 0); używany w kontenerze dla każdego `DeliveryKind`.

### Krok 12 — uniwersalny `DeliveryInboxProcessor` + `kind_var`

- **Zmiana**: nowy `shell/platform/infrastructure/messaging/delivery/processor/delivery_inbox_processor.py` (`DeliveryInboxProcessor(InboxProcessorBase)`) zastępuje 3 podprocesory; w `shell/platform/infrastructure/context.py` dodać `kind_var` (ContextVar); w `inbox_processor_base.py` `_ClaimedInboxRow` + `kind`/`contract_type`.
- **Jak**:
  - konstruktor: `session_factory`, `models: DeliveryModels`, `policies: Mapping[DeliveryKind, DeliveryPolicy]`, opcjonalnie `event_bus`/`message_bus`/`command_bus` + registry/upcastery per kind;
  - `_type_name(row)` → `row.contract_type`;
  - `_deserialize(row)` → po `DeliveryKind(row.kind)` wybiera `EventDeserializer`/`MessageDeserializer`/`CommandDeserializer`;
  - `_dispatch(obj)` → po kind: `event_bus.publish([obj])`/`message_bus.publish([obj])`/`command_bus.dispatch(obj)`;
  - `_causation_value(obj, row)` → po kind: `event_id.value`/`message_id.value`/`row.causation_id`;
  - retry/backoff/DLQ/lease: wartości **z `policies[kind]`** przekazane do `InboxProcessorBase`;
  - `kind_var` ustawiany w `_process_claimed_row` (z tracingiem) i resetowany w `finally` — bezpieczeństwo przy `max_concurrency > 1`.
- **Weryfikacja**: unified `test_delivery_inbox_processor.py` — ten sam cykl claim→process→ack dla event/message/command; test równoległości (`max_concurrency>1`) — brak przecieku `kind` między taskami (tracing+kind).

### Krok 13 — usunięcie starych procesorów

- **Zmiana**: usunąć `messaging/event/processor/event_inbox_processor.py`, `messaging/message/processor/message_inbox_processor.py`, `messaging/command/processor/command_inbox_processor.py`.
- **Jak**: po pełnym przestawieniu na `DeliveryInboxProcessor` (kroki 12 + 16) usunąć pliki i wszystkie importy.
- **Weryfikacja**: test architektury (import-linter/AST) blokuje te ścieżki importów; `rg "EventInboxProcessor|MessageInboxProcessor|CommandInboxProcessor"` → 0.

### Krok 14 — per-BC aliase modułowe modeli

- **Zmiana**: w 7 × `infrastructure/<bc>/persistence/sql/models/base.py` aliasy `EVENT_DELIVERY_MODELS`/`MESSAGE_DELIVERY_MODELS`/`COMMAND_DELIVERY_MODELS` → jeden `DELIVERY_MODELS = PERSISTENCE_DELIVERY_MODELS.delivery` (+ `InboxModel`/`OutboxModel`).
- **Jak**: podmienić importy i przekazy; BC: definition, execution, ingestion, project, scheduling, session, user.
- **Weryfikacja**: `rg "EVENT_DELIVERY_MODELS|MESSAGE_DELIVERY_MODELS|COMMAND_DELIVERY_MODELS"` → 0; importy bazowe przechodzą.

### Krok 15 — baseline per BC (tabele)

- **Zmiana**: w 7 × `migrations/baseline.py` lista `_TABLES` z 6 tabel (`outbox_event`...`inbox_command`) → 2 (`DELIVERY_MODELS.outbox.__table__`, `DELIVERY_MODELS.inbox.__table__`).
- **Jak**: podmienić wpisy `PERSISTENCE_DELIVERY_MODELS.events/messages/commands.*` na `...delivery.outbox/inbox`.
- **Weryfikacja**: `mypy`/`ruff` na baseline'ach; test metadata — każdy BC ma dokładnie `{inbox, outbox}` + audit/dedup/heartbeat.

### Krok 16 — kontenery per BC (processor, polityki, konsument, relay CLI)

- **Zmiana**: w 6 × `bootstrap/<bc>/container/*_core_container.py` `...events.inbox` → `...delivery.inbox` i budowa procesora → `DeliveryInboxProcessor` + `policies` per kind (event/message/command z `DeliveryPolicy`); konsument z jawnymi wzorcami routingu; `framework/.../cli/command/relay_command.py` → `DELIVERY_MODELS` bez `kind=`.
- **Jak**: podmienić rejestracje `inbox_model=` i konstruktory processorów; wstrzyknąć `Mapping[DeliveryKind, DeliveryPolicy]` z configu BC; bindować `event.#`/`message.#`/`command.#` wg obsługiwanych kontraktów.
- **Weryfikacja**: e2e `test_microservice_flow.py` przechodzi (event user→session); test kontenera — polityki obecne dla wszystkich kindów; `rg "events\.inbox|EventInboxProcessor"` w bootstrap → 0.

### Krok 17 — seed/builders per BC (dev/data)

- **Zmiana**: `ingestion_service/infrastructure/ingestion/seed/builders.py` + `seed/dev.py` — `build_outbox_event_model`/`build_inbox_event_model` → uniwersalne `build_outbox_model(kind, contract_type, ...)` / `build_inbox_model(kind, contract_type, ...)`.
- **Jak**: rozszerzyć sygnatury o `kind` i `contract_type`; metadane eventu tylko przy EVENT.
- **Weryfikacja**: seed dev.py uruchamia się; test e2e ingestion z seedem przechodzi.

### Krok 18 — migracja danych (Alembic, per BC)

- **Zmiana**: nowe tabele `outbox`/`inbox` + przeniesienie danych z 6 starych tabel + drop starych.
- **Jak** (jedna migracja na BC; workerzy wyłączone w oknie przejściowym):
  1. `create_table outbox`, `create_table inbox` (schema z sekcji 5);
  2. eventy:

```sql
INSERT INTO outbox (id, kind, contract_type, event_id, source_service, occurred_at,
                    aggregate_id, aggregate_name, schema_version, payload,
                    correlation_id, causation_id, published_at)
SELECT id, 'event', event_type, event_id, source_service, occurred_at,
       aggregate_id, aggregate_name, schema_version, payload,
       correlation_id, causation_id, published_at
FROM outbox_event;
```

  3. message i command (bez metadanych eventu):

```sql
INSERT INTO outbox (id, kind, contract_type, occurred_at, payload,
                    correlation_id, causation_id, published_at)
SELECT id, 'message', message_type, occurred_at, payload,
       correlation_id, causation_id, published_at FROM outbox_message;

INSERT INTO outbox (id, kind, contract_type, occurred_at, payload,
                    correlation_id, causation_id, published_at)
SELECT id, 'command', command_type, occurred_at, payload,
       correlation_id, causation_id, published_at FROM outbox_command;
```

  4. analogiczne `INSERT INTO inbox ... SELECT ... FROM inbox_event/inbox_message/inbox_command`
     (+ `status`, `next_attempt_at`, `received_at`, `schema_version`);
  5. weryfikacja liczników (poniżej) PRZED `drop_table`;
  6. `drop_table` starych 6 tabel; aktualizacja baseline (krok 15).
- **Weryfikacja** — akceptacja tylko, gdy delta = 0:

```sql
SELECT
  (SELECT count(*) FROM outbox_event)   AS delta_outbox_event,
  (SELECT count(*) FROM outbox_message) AS delta_outbox_message,
  (SELECT count(*) FROM outbox_command) AS delta_outbox_command,
  (SELECT count(*) FROM inbox_event)    AS delta_inbox_event,
  (SELECT count(*) FROM inbox_message)  AS delta_inbox_message,
  (SELECT count(*) FROM inbox_command)  AS delta_inbox_command;
```

  + `count(outbox WHERE kind='event') == count(outbox_event)` przed dropem + spot-check losowych kolumn (payload, correlation_id, published_at) 1:1. Zalecane: retention przed migracją (mniejszy wolumen).

### Krok 19 — testy architektury (nowe reguły)

- **Zmiana**: testy metadata/nazw/importów do aktualizacji i rozszerzenia.
- **Jak**:
  - `test_platform_event_delivery.py`, `test_platform_message_command_delivery.py` → unifikacja na `{inbox, outbox}`;
  - `test_bc_metadata_ownership.py`, `test_bc_delivery_table_ownership.py`, `test_database_metadata_isolation__*.py` (2) → `{"inbox","outbox"}`;
  - nowe reguły: zakaz nazw `outbox_event`/`inbox_event`/`outbox_message`/`inbox_message`/`outbox_command`/`inbox_command` w metadata BC; wymóg `CheckConstraint` dla `kind`/`contract_type` w modelach `outbox`/`inbox`; zakaz importów starych publisherów (`sql_message_outbox_publisher`, `sql_command_outbox_publisher`) i procesorów (`event_inbox_processor`...).
- **Weryfikacja**: cały zestaw `tests/architecture/` przechodzi.

### Krok 20 — testy platformy

- **Zmiana**: testy integracyjne/unitowe platformy na nowe modele i klasy.
- **Jak**: `tests/platform/integration/platform_delivery_models.py` → `DELIVERY_MODELS = PERSISTENCE_DELIVERY_MODELS.delivery`; `test_outbox_to_transport_relay.py` + `test_message_outbox_transport_relay.py` → jeden wariantowy test; `test_event_inbox_processor_refactored.py`, `test_event_message_inbox_processors.py`, `test_command_inbox_processor.py` → `test_delivery_inbox_processor.py`; `test_inbox_*` (claim/heartbeat/atomicity/replay/metrics/retention/readiness) i `test_pg_inbox_claim_concurrency.py` → modele `delivery.inbox` (semantyka bez zmian); `test_message_outbox.py` → nowy unified publisher; `test_envelope_codec.py` → + przypadek nieznanego `kind`.
- **Weryfikacja**: `pytest tests/platform/` przechodzi.

### Krok 21 — testy system/contracts/e2e

- **Zmiana**: `tests/system/test_microservice_flow.py`, `tests/system/test_transactional_semantics.py`, `tests/contracts/test_integration_event_transport_contract.py`, `tests/session_service/.../test_missing_integration_event.py` → `delivery.outbox/inbox`; `test_user_standalone_app.py`, `test_definition_standalone.py` → listy tabel bez starych 4.
- **Jak**: mechaniczna podmiana referencji (modele i nazwy tabel) przy zachowaniu asercji.
- **Weryfikacja**: e2e systemowe przechodzi (realny przepływ user→session przez Rabbit).

### Krok 22 — dokumentacja i skille

- **Zmiana**: `docs/inbox-outbox-architecture.md`; `shell/platform/doc/delivery-models.md`, `delivery-overview.md`, `relay.md`, `unit-of-work.md`, `transactional-outbox.md`, `inbox-processor.md`, `delivery-transport.md`, `session-scope.md`, `processed-delivery-dedup.md`, `tracing-context.md`, `metrics.md`, `readiness.md`, `replay.md`, `retention.md`; `shell/README.md`; skille: `shell-specific/tracing-context`, `integration-patterns/event-driven-integration/*`, `integration-patterns/idempotency-retry`, `pattern-standards/event-handler-structure/*`, `shell-specific/shell-architecture/references/infrastructure.md`.
- **Jak**: zamiana nazw tabel/klas (`outbox_event` → `outbox(kind)`, `EventInboxProcessor` → `DeliveryInboxProcessor` itd.) + opis nowych polityk per kind i `DeliveryKind`.
- **Weryfikacja**: `rg "outbox_event|EventInboxProcessor|SqlMessageOutboxPublisher"` w docs+skills → 0.

### Krok 23 — monitoring i alerty

- **Zmiana**: metryki per kind (claimed/processed/retried/dead_lettered/lag) + alert na wzrost DLQ; rejestracja w kontenerze procesora.
- **Jak**: dodać etykietę `kind` do metryk `InboxProcessorBase`/`DeliveryInboxProcessor`; alert gdy `dead_lettered` rośnie w oknie.
- **Weryfikacja**: test metryk — etykieta `kind` obecna; dashboard/alert zdefiniowany.

---

## 7. Kryteria zakończenia (definition of done)

1. Jeden `DeliveryModels`/`PersistenceDeliveryModels`; brak `event_delivery.py`, `message_delivery.py`, `command_delivery.py`.
2. Jeden `SqlDeliveryOutboxPublisher` działający **wyłącznie przez UoW**; brak `SqlMessageOutboxPublisher`, `SqlCommandOutboxPublisher`, `InMemoryMessageOutboxStore`, `FakeMessagePublisher`.
3. Jeden `DeliveryInboxProcessor`; brak trzech podprocesorów.
4. `stage_messages` i `stage_commands` realnie zapisywane do `outbox` atomowo ze stanem (test rollback potwierdza brak wierszy).
5. `kind` typu `DeliveryKind(StrEnum)` + `CheckConstraint`; test architektury blokuje gołe stringi i stare nazwy tabel.
6. Wire `EnvelopeCodec` bez zmian; nieznany `kind` odrzucany (nack + alert).
7. Kolejki konsumentów z jawnymi bindingami per kind; `mandatory=True`.
8. Migracje per BC kopiują 6 → 2 bez straty (weryfikacja delta = 0).
9. Metryki per kind i alerty DLQ włączone.
10. `run_tests.ps1` przechodzi bez błędów.

---

## 8. Ryzyka i sposób ich zamknięcia

| Ryzyko | Mitigacja |
|---|---|
| Zmiana UoW dotyka wszystkich agregatów | Kroki 4–6 i 14–16 etapami BC po BC; każdy BC w osobnym PR z pełnym testem |
| Migracja produkcyjna | Okno przejściowe z wyłączonymi workerami + weryfikacja delta=0 + retention przed migracją |
| Przeciek `kind` między taskami | `kind_var` ContextVar + reset w `finally` + test równoległości `max_concurrency>1` |
| Literówka kind / pusty contract_type | `CheckConstraint` w DB + `DeliveryKind` w kodzie + testy architektury |
| Regresja wire | Zamrożony kontrakt + `test_integration_event_transport_contract.py` w CI + `EnvelopeCodec` bez zmian |
| Ciche zgubienie przy braku kolejki | `mandatory=True` (nieroutowalny = błąd → retry/DLQ) |