# Przepływ komendy w SHELL — DROGA ASYNCHRONICZNA

Status: analiza stanu faktycznego kodu
Data: 2026-09-01
Zakres: delivery między Bounded Contextami przez transactional outbox → broker (RabbitMQ) → inbox → processor. Obejmuje **eventy** (`outbox_event`/`inbox_event`) oraz **async-komendy** (`outbox_command`/`inbox_command`).

---

## 0. Charakterystyka

- **Tryb**: `outbox → Relay → RabbitMQ → inbox → Processor → (Event|Command)Bus → Handler` — fire-and-forget, eventual consistency.
- **Gwarancja**: **at-least-once** (nie exactly-once). Mechanizmy idempotencji: unique `(source_service, outbox_id)` na inboxie + `processed_delivery` przed dispatch.
- **Dwie transakcje** per rekord: A = claim (lease), B = przetwarzanie + ack (jeden commit efekt + outbox + ack).
- **Dwa warianty tego samego szkieletu**: event (`event.<name>`) i async-komenda (`command.<name>`) — osobne tabele, wspólne klasy platformowe.

```mermaid
flowchart TD
    AGG[DomainEvent z mutacji] -->|commit atomowy z efektem| OB[(outbox_event / outbox_command)]
    OB -->|published_at IS NULL| REL[OutboxToTransportRelay.run_once]
    REL -->|EnvelopeCodec.encode| TR[Rabbit*DeliveryTransport]
    TR -->|publish persistent / mandatory / routing event.<name>| EX[(exchange shell.delivery topic)]
    EX -->|routing event.# / command.#| Q[(durable queue per BC)]
    Q --> HCON[RabbitInboxConsumer._on_message]
    HCON -->|decode + insert inbox + commit + ack| IB[(inbox_event / inbox_command PENDING)]
    IB --> PW[PollingWorker.poll]
    PW --> CLAIM[InboxClaimService.claim_batch]
    CLAIM -->|Transakcja A: PROCESSING + claimed_by + lease_until + commit| PROC[InboxProcessorBase._process_claimed_row]
    PROC -->|session scope / deserialize / tracing| DISP[EventInboxProcessor -> EventBus | CommandInboxProcessor -> CommandBus]
    DISP --> H[Handler, UoW w deferred mode]
    H -->|efekt + lokalny outbox + PROCESSED| ONE[Transakcja B: pojedynczy commit]
```

---

## 1. Producent (strona nadawcy)

### 1a. Event

| # | Krok | Plik:linia | Szczegóły |
|---|---|---|---|
| 1 | Zapis do outboxa | `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py:159-190` | W ścieżce synchronicznej event trafia do `outbox_event` atomowo z efektem (ten sam commit). W procesorze inbox — do **lokalnego** outboxa w deferred mode (flush + commit procesora). Wiersz ma `published_at = NULL` do czasu potwierdzonego transportu. |
| 2 | Relay | `shell/platform/infrastructure/messaging/event_transport/outbox_to_transport_relay.py:73-96` | `run_once()` w **jednej transakcji**: `SELECT ... WHERE published_at IS NULL ... FOR UPDATE SKIP LOCKED` (tylko PG, `:71/81-82`), buduje `IntegrationEventDeliveryEnvelope` (:98-112), dla każdego: `await transport.deliver(envelope)`, po czym ustawia `published_at` i `commit()` (:93-95). |
| 3 | Transport | `shell/platform/infrastructure/messaging/event_transport/rabbit/rabbit_event_delivery_transport.py:45-66` | `exchange.publish(Message(..., delivery_mode=PERSISTENT), routing_key=f"event.{name}", mandatory=True)`; publisher confirms + `on_return_raises`. |
| 4 | Envelope | `shell/platform/infrastructure/messaging/command_transport/envelope_codec.py:17-72` (event analogicznie) | JSON: kind, outbox_id, name, source_service, target_service, issued_at/occurred_at, schema_version, payload, correlation_id, causation_id. |

### 1b. Async-komenda (nadawca)

| # | Krok | Plik:linia | Szczegóły |
|---|---|---|---|
| 1 | Port | `shell/platform/application/ports/command/async_command_dispatcher.py:8` | `AsyncCommandDispatcher` — kontrakt „wyślij intencję asynchronicznie". |
| 2 | Dispatcher | `shell/platform/infrastructure/messaging/command/sql_command_outbox_writer.py:114-148` (`SqlAsyncCommandDispatcher`) | Rozwiązuje `CommandContract` (wire name, `target_service`), waliduje `target_service`, serializuje payload, `writer.append(scope.session, ...)` **bez commita** — atomy z UoW handlera. Wymaga aktywnego `DeliverySessionScope` (`:137-141`). |
| 3 | Writer (session) | `sql_command_outbox_writer.py:35-78` (`SqlCommandOutboxWriter.append`) | `session.add(outbox_command)` z `command_id`, `command_name`, `source_service`, `target_service`, `schema_version`, `issued_at`, payload, `correlation_id`/`causation_id` z kontekstu. **Nigdy nie wykonuje commit.** |
| 4 | Writer (standalone) | `sql_command_outbox_writer.py:81-111` (`StandaloneSqlCommandOutboxWriter`) | Własny commit na własnej sesji — TYLKO dla komend utworzonych poza UoW. Legacy: `sql_command_outbox_publisher.py:25-67`. |
| 5 | Relay | `shell/platform/infrastructure/messaging/command_transport/outbox_to_transport_relay.py:54-96` | Analogiczny do eventowego: `command.<command_name>` (`rabbit_command_delivery_transport.py:48`). |

> ⚠️ **Stan faktyczny**: nadawca async-komendy **nie jest podłączony w produkcji** — patrz §4.

---

## 2. Konsument (strona odbiorcy)

| # | Krok | Plik:linia | Szczegóły |
|---|---|---|---|
| 1 | Consumer → inbox | `shell/platform/infrastructure/messaging/event_transport/rabbit/rabbit_event_inbox_consumer.py:74-118` (command: `command_transport/rabbit/rabbit_command_inbox_consumer.py:74-118`) | `start()` deklaruje durable queue i binduje routing (domyślnie **`event.#` / `command.#`**). `_on_message`: dekoduj → `_persist(envelope)` → **insert + commit do inboxa** → `ack()`. Redeliveria idempotentna: `pg_insert(...).on_conflict_do_nothing()` + `UniqueConstraint(source_service, outbox_id)` (`event_delivery.py:49-53`, `command_delivery.py:56-60`). |
| 2 | Polling | `shell/platform/infrastructure/messaging/polling_worker.py:62-113` + `event_worker.py:18-63` | `run_delivery_workers` startuje consumerów i pętle `PollingWorker(task.run_once)`. Worker zapisuje heartbeat. |
| 3 | Claim (transakcja A) | `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py:72-119` | `claim_batch`: `SELECT ... (status IN (PENDING,RETRY) AND next_attempt_at <= now) OR (status=PROCESSING AND lease_until < now) ... FOR UPDATE SKIP LOCKED` (PG), ustawia `PROCESSING`/`claimed_by`/`lease_until`, **commit**. Krótka transakcja — zamek nie trzymany przez handler. |
| 4 | Walidacja + deserializacja + tracing | `inbox/inbox_processor_base.py:218-259` (`_process_claimed_row`) | `EnvelopeValidator.validate(...)` → `_deserialize(row)` → ustawienie `correlation_id_var`/`causation_id_var`. Błędy → `_schedule_failure` (RETRY/DLQ, `:416-463`; `max_retries=3`, backoff wykładniczy `:465-471`). |
| 5 | Przetwarzanie (transakcja B) | `inbox/inbox_processor_base.py:261-314` (`_process_in_transaction`) | Procesor **właściciel sesji**: `DeliverySessionScope(session)` → `set_session_scope` (`shell/platform/application/context/session_scope.py:26-49`). Dedup: `_is_duplicate` przez `ProcessedDeliveryStore` (`:316-319`). Dispatch: event → `EventBus.publish` (`event/processor/event_inbox_processor.py:105-106`), komenda → `CommandBus.dispatch` (`command/processor/command_inbox_processor.py:102-103`). |
| 6 | Handler w session scope | `sql_alchemy_uow_base.py:117-123` | UoW handlera **współdzieli sesję** procesora i **odracza commit** (`_deferred_commit=True`; `commit()` = flush, `:147-150`). |
| 7 | Ack atomowy | `inbox_processor_base.py:321-341` + `:307-311` | `_acknowledge_in_session`: warunkowy `UPDATE ... WHERE id AND status=PROCESSING AND claimed_by=worker` → `PROCESSED`. Potem `session.commit()` — **jeden commit czyszczy: efekt biznesowy + lokalny outbox (ponowny `_write_staged_outbox` w deferred) + status PROCESSED**. `rowcount=0` → `rollback` → `"failed"` (lease zgubiony). |
| 8 | Retry/DLQ | `inbox_processor_base.py:416-463` | `next_retry_count >= max_retries` lub `UNSUPPORTED_SCHEMA_VERSION` → `DEAD_LETTER` (log `critical`); w przeciwnym razie `RETRY` + `next_attempt_at = now + backoff`. |

**Idempotencja (zamyka at-least-once):**
- broker może dostarczyć 2× (duplikat z relay) → unique `(source_service, outbox_id)` na insert;
- processor może dostać ten sam rekord 2× (lease reclaim) → `processed_delivery` sprawdzany przed dispatch (`:273`), zapisywany atomowo z efektem (`:300-305`);
- ack warunkowy po `id + status + claimed_by` → nie potwierdzamy cudzego rekordu (`:321-341`).

---

## 3. Modele SQL

| Tabela | Unikalność / indeksy | Plik |
|---|---|---|
| `outbox_event` | `event_id` UNIQUE | `shell/platform/infrastructure/persistence/sql/models/event_delivery.py:26-41` |
| `inbox_event` | `uq_inbox_event_source_outbox (source_service, outbox_id)` + indeksy statusu | `event_delivery.py:43-67` |
| `outbox_command` | `uq_outbox_command_source_cmd (source_service, command_id)` + `ix_outbox_command_publish` | `shell/platform/infrastructure/persistence/sql/models/command_delivery.py:26-48` |
| `inbox_command` | `uq_inbox_command_source_outbox (source_service, outbox_id)` + indeksy statusu | `command_delivery.py:50-75` |
| wspólny lifecycle | `InboxStateMixin` (`status/next_attempt_at/lease_until/claimed_by/retry_count/error*`) | `shell/platform/infrastructure/persistence/sql/models/mixins/inbox_state.py:35-69` |

---

## 4. Wiring produkcyjny — co faktycznie jest podłączone

Na bazie `shell/project_service/bootstrap/project/main.py:63-82` i kontenera `project_core_container.py`:

| Komponent | Podłączony w produkcji? | Uwagi |
|---|---|---|
| `EventOutboxToTransportRelay` | ✅ tak (`main.py:80`) | Jedyne relay w każdej pętli `run_delivery_workers` wszystkich BC. |
| `RabbitEventInboxConsumer` + `EventInboxProcessor` | ✅ tak (`main.py:65-69`) | Kanał eventowy domknięty. |
| `RabbitCommandInboxConsumer` + `CommandInboxProcessor` | ✅ tak (odbiór, `main.py:70-74`) | Strona odbiorcy async-komend działa. |
| `CommandOutboxToTransportRelay` | ❌ **nie** | Nigdzie w `run_delivery_workers` — tylko w testach (`shell/tests/platform/integration/sql_sqlite/test_command_inbox_processor.py:97`). |
| `SqlAsyncCommandDispatcher` / `SqlCommandOutboxWriter` / `StandaloneSqlCommandOutboxWriter` / `SqlCommandOutboxPublisher` | ❌ **nie** (brak wywołania w kodzie produkcyjnym) | Klasy istnieją, używane wyłącznie w testach / `__init__`. |

**Wniosek:** async-komenda ma **domkniętą stronę odbioru, ale otwarty tor nadawczy**. Żaden BC nie zapisuje komendy do `outbox_command`, a nawet gdyby zapisał, nie startuje `CommandOutboxToTransportRelay` — wiersz zostałby w `outbox_command` bez `published_at` na zawsze.

---

## 5. Analiza transakcyjności — gdzie NIE zgubimy, gdzie grozi utrata

### 5.1 Producent (zapis outboxa) — DOBRZE

| Ogniwo | Mechanizm | Utrata? |
|---|---|---|
| Mutacja + outbox + audit | jedna transakcja `sql_alchemy_uow_base.py:142-190` | ❌ nie atomowo — crash przed commitem → spójny rollback. |
| Błąd serializacji | wyjątek propaguje (`critical` + `raise` w publisherach) | ❌ nie — wiersz nie powstaje lub batch nie jest oznaczany. |

### 5.2 Relay (outbox → broker) — UWAGA: duplikaty i długie locki

| Punkt | Ryzyko | Ocena |
|---|---|---|
| `FOR UPDATE SKIP LOCKED` trzymane przez całe wywołanie sieciowe (`outbox_to_transport_relay.py:74-95`) | wolny broker → długie locki DB na całej partii | ⚠️ nie utrata, ale presja na DB / możliwy timeout sesji. |
| Publikacja częściowa partii (deliver OK dla części, błąd dla kolejnej) | wyjątek → brak `commit()` → żaden wiersz nie dostaje `published_at` → już-opublikowane wiersze idą ponownie | ⚠️ **duplikaty** w brokerze — łagodzone dedupem `(source_service, outbox_id)` + `processed_delivery`. |
| Crash po publish, przed commit | jak wyżej | ⚠️ duplikat, bezpieczny dedupem. |
| Błąd transportu → wyjątek z `deliver` | wiersz zostaje `PENDING` → retry w kolejnym poll | ✅ nie utrata (zamierzony retry). |
| Brak `attempt_count/next_attempt_at/last_error` na outboxie | zatruty wiersz blokuje/opóźnia partię na każdym poll; brak backoff/DLQ producenta | ⚠️ nie utrata, ale brak dojrzałego retry. |

### 5.3 Broker RabbitMQ — właściwie skonfigurowany

| Punkt | Ocena |
|---|---|
| `publisher_confirms=True` + `mandatory=True` + `on_return_raises=True` (`rabbit_*_delivery_transport.py:73-76`) | ✅ unroutable message nie jest „pozornym sukcesem": wyjątek → wiersz nieoznaczony → retry. |
| PERSISTENT + durable exchange/queue | ✅ przetrwanie restartu brokera. |
| **Brak dead-letter dla consumerów** | ⚠️ patrz 5.4. |

### 5.4 Consumer (broker → inbox) — JEDYNY PRAWDZIWY PUNKT UTRATY

| Punkt | Ryzyko | Ocena |
|---|---|---|
| Decode failure → `message.reject(requeue=False)` (`rabbit_event_inbox_consumer.py:77-80`, `rabbit_command_inbox_consumer.py:77-80`) | zły JSON / zły `kind` / braki pól → **wiadomość odrzucona bez requeue → utracona**. Brak DLQ (brak `x-dead-letter-exchange`) | ❌ **UTRATA** (at-most-once dla uszkodzonych kopert). |
| Insert/commit nieudany → `reject(requeue=True)` | DB chwilowo niedostępna → redelivery | ✅ nie utrata; ryzyko pętli hot redelivery przy trwałej awarii DB (brak max-delivery/TTL) — nie utrata, ale backlog. |
| Crash po commit inboxa, przed ack | redelivery → `on_conflict_do_nothing` → wiersz już jest → ack | ✅ nie utrata, idempotentny. |
| Ack dopiero po trwałym insert | — | ✅ zgodnie z wymogiem „ack dopiero po trwałym zapisie do inboxa". |

### 5.5 Processor (inbox → handler) — NAJBEZPIECZNIEJSZE OGNIWO

| Punkt | Mechanizm | Ocena |
|---|---|---|
| Efekt + lokalny outbox + ack w jednym commicie (transakcja B) | `inbox_processor_base.py:307-311` + deferred UoW | ✅ brak utraty i brak podwójnego efektu: awaria przed commitem cofa wszystko; po commicie → `PROCESSED`. |
| Lease wygasł / reclaim | `inbox_claim_service.py:96-99` + warunkowy ack (rowcount) | ✅ rowcount=0 → rolback → nie potwierdzanie cudzego rekordu. |
| Handler rollback → `scope.rolled_back` | `sql_alchemy_uow_base.py:192-199` + `inbox_processor_base.py:292-298` | ✅ zamiast ack — `_schedule_failure(RETRY)`. |
| Dedup `processed_delivery` | `:273` (przed dispatch) + `:300-305` (atomowo z efektem) | ✅ double processing zablokowany. |
| RETRY/DLQ z backoffem | `:416-471` | ✅ wyczerpanie retry → `DEAD_LETTER` z logiem `critical`. |

### 5.6 Podsumowanie ryzyk „zgubienia komendy"

1. **❌ Utrata (hard)**: `reject(requeue=False)` dla niezdekodowanych kopert — wiadomość ginie bez śladu (brak DLQ). Rozwiązanie: dead-letter exchange/kolejka albo zapis „poison" do bazy przed reject.
2. **❌ Async-komenda bez toru nadawczego w produkcji**: brak producenta (`SqlAsyncCommandDispatcher`) **oraz** brak `CommandOutboxToTransportRelay` w `run_delivery_workers` wszystkich BC. Komenda zapisana do `outbox_command` nigdy nie zostałaby opublikowana → **utrata „po cichu" przez brak workera** (największa rozbieżność względem `command.md` P0/P1).
3. ⚠️ **Duplikaty z relay** przy częściowym błędzie partii / crash między publish a commit — łagodzone dedupem, nie eliminowane u producenta.
4. ⚠️ Routing szeroki `event.#`/`command.#` (`rabbit_*_inbox_consumer.py:52`) — każdy BC odbiera wszystko; kolizja wire-name (registry oparte o `__name__` klasy, `shell/platform/infrastructure/serialization/registries/command_registry.py:19-38`).
5. ⚠️ Long lock w relay podczas I/O sieci — nie utrata, ale ryzyko operacyjne.
6. ⚠️ Outbox bez retry-backoff/DLQ po stronie producenta — zatruty wiersz może blokować partię.

**Gdzie komenda/event NIE jest tracona (dobre praktyki obecne):**
- UoW deferred + `DeliverySessionScope` — jeden commit na efekt+outbox+ack;
- dedup przy zapisie inboxa (unique `source_service+outbox_id`);
- dedup przed dispatch (`processed_delivery`);
- lease/claim/reclaim z warunkowym ack;
- publisher confirms + mandatory + re-raise na błędach;
- retry/DLQ inbox z backoffem i `max_retries`.

---

## 6. Rekomendacje (najmniejsze do największych)

1. **Consumer DLQ**: dead-letter exchange/queue albo `PersistAndRejectPoison`, aby uszkodzona koperta nie znikała.
2. **Domknąć tor komend**: włączyć `CommandOutboxToTransportRelay` jako osobny worker w `run_delivery_workers` BC wysyłających komendy; podłączyć `SqlAsyncCommandDispatcher` do portu i użyć w handlerze (zgodnie z `command.md` P0/P1).
3. **Relay**: rozbić na krótką transakcję claim + publish poza transakcją + warunkowy `mark published` (`command.md §8`) — ograniczy duplikaty i długie locki.
4. **Retry state outboxa** (`attempt_count`, `next_attempt_at`, `last_error`) + DLQ producenta (`command.md §8`).
5. **Routing per-komenda** (`command.<target>.<name>` zamiast `command.#`, `command.md §9`).
6. **Stabilny wire-name** zamiast `__name__` klasy (`command.md §4`).

---

## 7. Kluczowe pliki

- `shell/platform/infrastructure/messaging/event_transport/outbox_to_transport_relay.py`
- `shell/platform/infrastructure/messaging/command_transport/outbox_to_transport_relay.py`
- `shell/platform/infrastructure/messaging/event_transport/rabbit/rabbit_event_delivery_transport.py`
- `shell/platform/infrastructure/messaging/command_transport/rabbit/rabbit_command_delivery_transport.py`
- `shell/platform/infrastructure/messaging/event_transport/rabbit/rabbit_event_inbox_consumer.py`
- `shell/platform/infrastructure/messaging/command_transport/rabbit/rabbit_command_inbox_consumer.py`
- `shell/platform/infrastructure/messaging/inbox/{inbox_claim_service,inbox_processor_base,processed_delivery_store,envelope_validator}.py`
- `shell/platform/infrastructure/messaging/event/processor/event_inbox_processor.py`
- `shell/platform/infrastructure/messaging/command/processor/command_inbox_processor.py`
- `shell/platform/infrastructure/messaging/command/sql_command_outbox_writer.py`
- `shell/platform/infrastructure/messaging/polling_worker.py`
- `shell/platform/infrastructure/messaging/event/event_worker.py`
- `shell/platform/application/context/session_scope.py`
- `shell/platform/infrastructure/persistence/sql/models/{event_delivery,command_delivery,mixins/inbox_state}.py`
- `shell/project_service/bootstrap/project/main.py` (wiring)
