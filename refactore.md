# Plan refaktoryzacji `shell/platform`

Status: plan do wykonania, bez zmian produkcyjnych.

Cel: uporzadkowac platforme wedlug odpowiedzialnosci, poprawic nazwy modulow i ograniczyc mieszanie kontraktow, mechanizmow wykonawczych oraz adapterow technicznych.

## 1. Zasady migracji

1. Nie zmieniac granicy `shell/platform` jako wspolnej warstwy technicznej.
2. Nie przenosic do platformy kodu zawierajacego pojecia bounded contextu.
3. Najpierw dodac nowe sciezki i kompatybilne re-eksporty, a dopiero potem aktualizowac importy konsumentow.
4. Nie laczyc bez potrzeby zmian strukturalnych ze zmiana publicznych kontraktow klas.
5. Po kazdym etapie uruchamiac testy importow, testy platformy i testy delivery.
6. Usuwac stare sciezki dopiero po sprawdzeniu, ze nie pozostaly importy produkcyjne, testowe ani skrypty.

## 2. Docelowa topologia

```text
shell/platform/
├── domain/
│   ├── building_blocks/
│   ├── events/
│   ├── errors/
│   ├── ports/
│   └── value_objects/
├── application/
│   ├── buses/
│   ├── execution_context/
│   ├── integration/
│   │   ├── contracts/
│   │   ├── events/
│   │   └── messages/
│   └── ports/
├── infrastructure/
│   ├── configuration/
│   ├── http/
│   ├── id_generation/
│   ├── observability/
│   │   ├── health/
│   │   ├── logging/
│   │   └── metrics/
│   ├── persistence/
│   ├── serialization/
│   └── delivery/
│       ├── channels/
│       │   ├── commands/
│       │   ├── events/
│       │   └── messages/
│       ├── inbox/
│       ├── outbox/
│       ├── processors/
│       ├── relays/
│       ├── retention/
│       ├── serialization/
│       ├── transport/
│       └── workers/
├── framework/
│   ├── api/
│   └── cli/
├── bootstrap/
└── types/                 # pozostaje tymczasowo, do audytu semantycznego
```

## 3. Domenowe building blocks

### 3.1 `domain/base` -> `domain/building_blocks`

Przesunac:

- `domain/base/entity.py` -> `domain/building_blocks/entity.py`
- `domain/base/aggregate_root.py` -> `domain/building_blocks/aggregate_root.py`
- `domain/base/value_object.py` -> `domain/building_blocks/value_object.py`
- `domain/base/entity_id.py` -> `domain/building_blocks/entity_id.py`

Dlaczego:

- `base` jest nazwa techniczna i nie opisuje odpowiedzialnosci.
- `building_blocks` jasno wskazuje, ze sa to bazowe klocki DDD uzywane przez bounded contexty.
- Nie zmieniac nazw klas ani ich API.

### 3.2 `domain/exceptions` -> `domain/errors`

Przesunac:

- `domain/exceptions/domain_error.py` -> `domain/errors/domain_error.py`
- `domain/exceptions/concurrent_modification_error.py` -> `domain/errors/concurrent_modification_error.py`

Dlaczego:

- Modul opisuje kontrakty bledow domenowych, a nie mechanizm rzucania wyjatkow.
- `errors` jest spojne z nazewnictwem warstwy aplikacyjnej i lepiej opisuje zawartosc.

### 3.3 `domain/messages` -> `domain/domain_messages`

Przesunac:

- `domain/messages/domain_message.py` -> `domain/domain_messages/domain_message.py`

Dlaczego:

- `messages` jest zbyt ogolne i latwo pomylic je z komunikatami aplikacyjnymi lub transportowymi.
- Nazwa ma wskazywac, ze chodzi o wiadomosci domeny.

### 3.4 `domain/events` pozostaje bez zmiany

Pozostawic:

- `domain/events/domain_event.py`
- `domain/events/aggregate_deleted_event.py`
- `domain/events/aggregate_restored_event.py`

Dlaczego:

- `events` jest jednoznaczne w obrebie domeny.
- Nie ma korzysci z dodatkowego poziomu katalogu.

### 3.5 `domain/ports` pozostaje bez zmiany

Pozostawic:

- `domain/ports/identity.py`
- `domain/ports/log.py`
- `domain/ports/repository_port.py`
- `domain/ports/time.py`

Dlaczego:

- Sa to porty domenowe i ich lokalizacja jest zgodna z architektura hexagonalna.
- Nie przenosic ich do `application/ports`, poniewaz dotycza abstrakcji wymaganych przez domene.

## 4. Audyt domenowych value objects

### 4.1 `domain/value_objects` pozostaje jako katalog techniczny tylko dla typow generycznych

Pozostawic w platformie po audycie uzycia:

- `aggregate_id.py`
- `event_id.py`
- `message_id.py`
- `created_at.py`
- `changed_at.py`
- `deleted_at.py`
- `occurred_at.py`
- `timestamp.py`
- `version.py`
- `schema_version.py`
- `exists_result.py`
- `inbox_status.py`, jezeli status jest wspolny dla calego delivery.

### 4.2 Kandydaci do przeniesienia do bounded contextu

Zweryfikowac uzycie i przeniesc poza platforme, jezeli sa uzywane tylko przez jeden kontekst:

- `edge_type.py`
- `state_direction.py`
- `workflow_reference.py`
- `semantic_data.py`
- `condition_expression.py`
- `mode.py`
- `reason.py`
- `state_data.py`
- `aggregate_name.py`, jezeli reprezentuje nazwe konkretnego agregatu zamiast generycznego identyfikatora.

Dlaczego:

- Sama lokalizacja i nazwa nie wystarcza, jezeli typ zawiera jezyk biznesowy konkretnego BC.
- Platforma powinna udostepniac tylko typy, ktore mozna testowac bez importowania bounded contextu.
- Ten etap wymaga analizy importow; nie wykonywac go mechanicznie.

## 5. Warstwa application

### 5.1 `application/bus` -> `application/buses`

Przesunac:

- `application/bus/command_bus.py` -> `application/buses/command_bus.py`
- `application/bus/query_bus.py` -> `application/buses/query_bus.py`
- `application/bus/event_bus.py` -> `application/buses/event_bus.py`
- `application/bus/message_bus.py` -> `application/buses/message_bus.py`
- `application/bus/event_bus_publisher.py` -> `application/buses/event_bus_publisher.py`
- `application/bus/message_bus_publisher.py` -> `application/buses/message_bus_publisher.py`

Dlaczego:

- Katalog zawiera kilka magistral, wiec liczba pojedyncza jest mylaca.
- Wszystkie klasy nadal pozostaja w warstwie application, bo sa mechanizmami aplikacyjnymi, nie adapterami infrastruktury.

### 5.2 `application/context` -> `application/execution_context`

Przesunac:

- `application/context/correlation_id.py` -> `application/execution_context/correlation_id.py`
- `application/context/causation_id.py` -> `application/execution_context/causation_id.py`
- `application/context/session_scope.py` -> `application/execution_context/session_scope.py`

Dlaczego:

- `context` nie mowi, czy chodzi o kontekst HTTP, transakcji, sesji czy logowania.
- `execution_context` obejmuje correlation, causation i scope aktywnego wykonania.

### 5.3 `application/contracts` -> `application/integration/contracts`

Przesunac:

- `application/contracts/contract_catalog.py` -> `application/integration/contracts/contract_catalog.py`

Dlaczego:

- Katalog dotyczy publicznych kontraktow komunikacji, a nie ogolnych kontraktow aplikacyjnych.
- Nowa sciezka odroznia go od portow i kontraktow wewnetrznych.

### 5.4 `application/events` -> `application/integration/events`

Przesunac:

- `application/events/integration_event.py` -> `application/integration/events/integration_event.py`

Dlaczego:

- Integration Event jest komunikatem granicy systemu, nie zwyklym eventem aplikacyjnym.
- Nazwa odroznia go od `domain/events`.

### 5.5 `application/messages` -> `application/integration/messages`

Przesunac:

- `application/messages/integration_message.py` -> `application/integration/messages/integration_message.py`

Dlaczego:

- To ten sam powod co dla Integration Event.
- Oba typy powinny byc widoczne jako jedna rodzina kontraktow integracyjnych.

### 5.6 `application/ports` pozostaje, ale zostanie podzielone tematycznie

Pozostawic katalog glowny `application/ports`, a pliki uporzadkowac nastepujaco:

- `config.py`, `filesystem.py`, `identity.py`, `metrics.py`, `readiness.py`, `seed.py` -> `application/ports/runtime/`
- `delivery_transport.py`, `delivery_dedup_store.py`, `messaging.py` -> `application/ports/delivery/`
- `unit_of_work.py` -> `application/ports/persistence/`
- `ports.py` -> usunac po przeniesieniu re-eksportow do odpowiednich `__init__.py`.

Dlaczego:

- `ports.py` jest agregatem o niejasnej odpowiedzialnosci.
- Porty runtime, delivery i persistence maja inne cykle zmian i innych adapterow.
- Nie zmieniac nazw Protocoli w pierwszym etapie.

## 6. Infrastruktura ogolna

### 6.1 `infrastructure/context/client.py` -> `infrastructure/http/correlation_id_client.py`

Przesunac:

- `infrastructure/context/client.py` -> `infrastructure/http/correlation_id_client.py`

Dlaczego:

- Klasa jest klientem HTTP i propaguje correlation ID.
- `context` jest mylaca nazwa, bo prawdziwy kontekst wykonania jest w application.

### 6.2 `infrastructure/identity` -> `infrastructure/id_generation`

Przesunac:

- `infrastructure/identity/uuid_id_generator.py` -> `infrastructure/id_generation/uuid_id_generator.py`

Dlaczego:

- Obecny katalog moze sugerowac uwierzytelnianie lub tozsamosc uzytkownika.
- Klasa generuje identyfikatory techniczne, wiec `id_generation` jest precyzyjne.

### 6.3 `infrastructure/time` -> `infrastructure/clock`

Przesunac:

- `infrastructure/time/system_clock.py` -> `infrastructure/clock/system_clock.py`

Dlaczego:

- Adapter implementuje port `Clock`, a nie obsluguje dowolny zakres czasu.
- Nazwa katalogu powinna odpowiadac kontraktowi domenowemu.

### 6.4 `infrastructure/mapping` -> `infrastructure/integration_mapping`

Przesunac:

- `infrastructure/mapping/integration_mapping_error.py` -> `infrastructure/integration_mapping/integration_mapping_error.py`
- `infrastructure/mapping/reflective_integration_mapper.py` -> `infrastructure/integration_mapping/reflective_integration_mapper.py`

Dlaczego:

- Moduly mapuja integration events/messages, a nie dowolne obiekty aplikacji.
- Usuwa to niejednoznacznosc z mapperami DTO i mapperami ORM w bounded contextach.

### 6.5 `infrastructure/logging` + `infrastructure/metrics` + `infrastructure/health` -> `infrastructure/observability`

Przesunac:

- `infrastructure/logging/*` -> `infrastructure/observability/logging/`
- `infrastructure/metrics/logging_metrics_backend.py` -> `infrastructure/observability/metrics/logging_metrics_backend.py`
- `infrastructure/health/sql_readiness_probe.py` -> `infrastructure/observability/health/sql_readiness_probe.py`

Dlaczego:

- Logowanie, metryki i readiness sa wspolnymi mechanizmami obserwowalnosci i operacji.
- `sql_readiness_probe.py` pozostaje adapterem infrastruktury, ale jest logicznie powiazany z monitorowaniem stanu uslugi.

Nie zmieniac nazw klas ani zachowania publisherow audytowych w tej fazie.

### 6.6 `infrastructure/configuration` pozostaje bez zmiany

Pozostawic:

- `infrastructure/configuration/shell_config.py`

Dlaczego:

- `configuration` jasno opisuje odpowiedzialnosc.
- Zmiana nazwy nie przynioslaby istotnej korzysci.

## 7. Delivery i komunikacja

### 7.1 `infrastructure/messaging` -> `infrastructure/delivery`

Przeniesc caly katalog `infrastructure/messaging` do `infrastructure/delivery`, ale dodatkowo rozdzielic pliki wedlug odpowiedzialnosci.

### 7.2 Workery

Przesunac:

- `infrastructure/messaging/polling_worker.py` -> `infrastructure/delivery/workers/polling_worker.py`
- `infrastructure/messaging/worker_heartbeat.py` -> `infrastructure/delivery/workers/worker_heartbeat.py`

Dlaczego:

- Worker steruje cyklem pracy, backoffem i shutdownem; nie jest konkretnym typem komunikatu.

### 7.3 Kanaly komunikacji

Przesunac:

- `messaging/command/*` -> `delivery/channels/commands/*`
- `messaging/event/*` -> `delivery/channels/events/*`
- `messaging/message/*` -> `delivery/channels/messages/*`

Dlaczego:

- `command`, `event` i `message` sa trzema kanalami/protokolami delivery.
- Katalog `channels` jasno odroznia je od wspolnych procesorow, transportu i lifecycle.

### 7.4 Inbox

Pozostawic nazwy plikow, ale przeniesc:

- `messaging/inbox/*` -> `delivery/inbox/*`

Dlaczego:

- Inbox jest osobnym obszarem lifecycle delivery: claim, walidacja, replay, retencja i deduplikacja.

Nastepnie rozdzielic klasy:

- `inbox_claim_service.py`, `inbox_processor_base.py`, `inbox_batch_result.py` -> `delivery/inbox/processing/`
- `inbox_replay_service.py`, `delivery_retention_service.py` -> `delivery/inbox/operations/`
- `processed_delivery_store.py`, `inbox_metrics_service.py` -> `delivery/inbox/state/`
- `envelope_validator.py` -> `delivery/inbox/validation/`

### 7.5 Outbox

Przesunac:

- `messaging/memory_outbox_store/*` -> `delivery/outbox/memory/*`
- klasy publisherow z `command`, `event` i `message` -> odpowiednie `delivery/channels/*/publishers/`

Dlaczego:

- In-memory outbox jest adapterem outbox, a nie ogolnym magazynem pamieci.
- Publisher zapisuje komunikat do outboxa; powinien byc widoczny w strukturze kanalu i outboxa.

### 7.6 Relaye

Przesunac:

- `command/*outbox_to_inbox_relay.py` -> `delivery/relays/command_outbox_to_inbox_relay.py`
- `event/*outbox_to_inbox_relay.py` -> `delivery/relays/event_outbox_to_inbox_relay.py`
- `message/*outbox_to_inbox_relay.py` -> `delivery/relays/message_outbox_to_inbox_relay.py`
- `transport/outbox_to_transport_relay.py` -> `delivery/relays/outbox_to_transport_relay.py`

Dlaczego:

- Relay jest etapem przeplywu, a nie implementacja konkretnego procesora kanalu.
- Wspolna lokalizacja ulatwi znalezienie wszystkich przejsc outbox -> inbox/transport.

### 7.7 Transport RabbitMQ

Przesunac:

- `messaging/transport/envelope_codec.py` -> `delivery/transport/envelope_codec.py`
- `messaging/transport/rabbit/*` -> `delivery/transport/rabbit/*`

Dlaczego:

- Transport opisuje zewnetrzny mechanizm dostarczenia.
- RabbitMQ jest konkretnym adapterem transportowym, a nie osobnym mechanizmem messaging.

### 7.8 Serializacja delivery

Przesunac:

- `messaging/serialization/command_deserializer.py` -> `delivery/serialization/command_deserializer.py`
- obecne `infrastructure/serialization/event_*`, `message_*`, `type_registry.py`, `upcaster.py` -> `delivery/serialization/`

Docelowo rozdzielic na:

- `delivery/serialization/registries/`
- `delivery/serialization/serializers/`
- `delivery/serialization/deserializers/`
- `delivery/serialization/upcasting/`

Dlaczego:

- Rejestry, serializery i upcastery sa elementami tego samego procesu transportowego.
- Nazwa `infrastructure/serialization` jest zbyt ogolna, bo chodzi przede wszystkim o komunikaty delivery.

## 8. Retencja i CLI

Przesunac:

- `infrastructure/cli/retention.py` -> `infrastructure/delivery/retention/retention_service.py`
- komenda uruchamiajaca retencje, jezeli istnieje, -> `framework/cli/commands/retention.py`

Dlaczego:

- Polityka retencji jest logika techniczna delivery.
- CLI powinno tylko parsowac argumenty i wywolac usluge, nie byc wlascicielem retencji.

## 9. `infrastructure/persistence`

### 9.1 Elementy pozostajace

Pozostawic:

- `persistence/in_memory_repository.py`
- `persistence/sql_alchemy_uow_base.py`
- `persistence/sql/*`

Dlaczego:

- Sa to rzeczywiste generyczne adaptery persystencji.

### 9.2 Fakes

Przeniesc:

- `persistence/memory/fake_clock.py` -> `platform/testing/fakes/fake_clock.py`
- `persistence/memory/fake_event_publisher.py` -> `platform/testing/fakes/fake_event_publisher.py`
- `persistence/memory/fake_id_generator.py` -> `platform/testing/fakes/fake_id_generator.py`
- `persistence/memory/fake_logger.py` -> `platform/testing/fakes/fake_logger.py`
- `persistence/memory/fake_message_publisher.py` -> `platform/testing/fakes/fake_message_publisher.py`
- `persistence/memory/fake_task_loader.py` -> `platform/testing/fakes/fake_task_loader.py`

Dlaczego:

- Te klasy nie sa adapterami persistence.
- Ich obecna lokalizacja utrudnia znalezienie test doubles i sugeruje bledna odpowiedzialnosc.

`InMemoryRepository` pozostaje w persistence. In-memory outbox przenosimy do delivery/outbox/memory, a nie do testing.

## 10. `types`

### 10.1 `types/json_str.py` -> `infrastructure/serialization/json_string.py`

Przeniesc po sprawdzeniu wszystkich importow:

- `types/json_str.py` -> `infrastructure/serialization/json_string.py`

Dlaczego:

- Jest to techniczny wrapper serializacyjny, a nie samodzielna domenowa wartosc biznesowa.
- `json_str.py` jest mniej czytelne niz `json_string.py`.

Do czasu zakonczenia migracji pozostawic re-eksport z `shell.platform.types.json_str`.

## 11. Bootstrap i framework

### 11.1 `framework` pozostaje

Pozostawic:

- `framework/api/*`
- `framework/api/middleware/*`
- `framework/api/models/*`
- `framework/api/ws/*`
- `framework/cli/*`

Nie przenosic middleware do infrastruktury.

Dlaczego:

- Middleware, modele API i parser CLI sa adapterami driving-side.
- Ich wlascicielem jest framework, nawet jezeli korzystaja z portow platformy.

### 11.2 `bootstrap` pozostaje

Pozostawic:

- `bootstrap/buses/buses.py`
- `bootstrap/logging/setup_logging.py`

Ewentualnie pozniej przemianowac `bootstrap/buses` na `bootstrap/runtime/buses`, jezeli pojawi sie wiecej konfiguratorow runtime. Nie robic tego w pierwszym etapie, bo obecna nazwa jest wystarczajaco jednoznaczna.

## 12. Re-eksporty i kompatybilnosc

1. W nowych katalogach zachowac te same nazwy klas.
2. W starych `__init__.py` dodac czasowe re-eksporty z nowych sciezek.
3. Nie definiowac klas ponownie w starych modulach.
4. Oznaczyc stare sciezki jako deprecated dopiero po aktualizacji wszystkich importow.
5. Zaktualizowac importy w:
   - bounded contexts,
   - composition roots,
   - testach platformy,
   - testach architektury,
   - skryptach generujacych registry,
   - dokumentacji platformy.
6. Po jednym pelnym wydaniu usunac stare moduly kompatybilnosci, jezeli nie sa uzywane poza repozytorium.

## 13. Testy i reguly architektury

Dodac lub rozszerzyc testy:

1. `test_platform_delivery_topology`:
   - procesory tylko w `delivery/inbox` lub `delivery/processors`,
   - transport tylko w `delivery/transport`,
   - relay tylko w `delivery/relays`,
   - worker tylko w `delivery/workers`.
2. `test_platform_persistence_topology`:
   - fake’i nie znajduja sie pod `persistence`,
   - modele SQL i UoW pozostaja pod `persistence`.
3. `test_platform_no_bc_value_objects`:
   - platformowe value objects nie moga importowac bounded contextow,
   - kandydaci biznesowi musza miec jawne uzasadnienie pozostania w platformie.
4. Istniejace testy importow:
   - `test_platform_does_not_import_bounded_contexts`,
   - `test_platform_does_not_import_other_layers`,
   - testy registry i delivery.
5. Testy regresji importow wszystkich aktualnych publicznych klas.

## 14. Kolejnosc wykonania

### Etap 1: przygotowanie

1. Wygenerowac liste wszystkich importow `shell.platform`.
2. Zidentyfikowac publiczne re-eksporty w `__init__.py`.
3. Dodac testy docelowej topologii bez przenoszenia kodu.
4. Potwierdzic, ze obecna branza przechodzi testy architektury.

### Etap 2: najbezpieczniejsze nazwy

1. `application/bus` -> `application/buses`.
2. `application/context` -> `application/execution_context`.
3. `infrastructure/context/client.py` -> `infrastructure/http/correlation_id_client.py`.
4. `infrastructure/mapping` -> `infrastructure/integration_mapping`.
5. `infrastructure/identity` -> `infrastructure/id_generation`.
6. `infrastructure/time` -> `infrastructure/clock`.

### Etap 3: delivery

1. Utworzyc `infrastructure/delivery`.
2. Przeniesc workery, inbox, outbox, relaye, procesory i transport.
3. Rozdzielic kanaly command/event/message.
4. Zaktualizowac composition roots i testy.
5. Uruchomic testy platform delivery oraz testy integracyjne SQLite/RabbitMQ, jezeli sa dostepne.

### Etap 4: persistence i test doubles

1. Wydzielic fakes do `platform/testing/fakes`.
2. Pozostawic generyczne repozytoria i UoW w persistence.
3. Przeniesc in-memory outbox do `delivery/outbox/memory`.

### Etap 5: domena i value objects

1. `domain/base` -> `domain/building_blocks`.
2. `domain/exceptions` -> `domain/errors`.
3. `domain/messages` -> `domain/domain_messages`.
4. Audytowac kazdy value object pod katem generycznosci.
5. Przenosic typy biznesowe do wlascicwych bounded contextow dopiero po potwierdzeniu uzycia.

### Etap 6: sprzatanie

1. Zaktualizowac dokumentacje w `shell/platform/doc`.
2. Usunac stare re-eksporty i sciezki po okresie kompatybilnosci.
3. Uruchomic pelne testy architektury:

```powershell
.\.venv\Scripts\python.exe -m pytest shell/tests/architecture -x
```

4. Uruchomic testy platformy:

```powershell
.\.venv\Scripts\python.exe -m pytest shell/tests/platform -q
```

5. Sprawdzic brak pozostalych importow starych sciezek.

## 15. Elementy, ktorych nie zmieniac

1. Nie przenosic kodu bounded contextow do platformy.
2. Nie laczyc `domain`, `application` i `infrastructure` w jeden katalog `shared`.
3. Nie przenosic routerow, middleware ani modeli API do infrastructure.
4. Nie zmieniac nazw klas i Protocoli podczas samego porzadkowania katalogow.
5. Nie zmieniac kontraktu event registry bez osobnego planu migracji.
6. Nie rozdzielac platformowej implementacji inbox/outbox na kopie per bounded context.
7. Nie uruchamiac `deploy.ps1` jako zwyklego kroku walidacji, poniewaz skrypt wykonuje rowniez commit.

## 16. Kryterium zakonczenia

Refaktoryzacje uznac za zakonczona, gdy:

- kazdy modul delivery mozna znalezc po jego odpowiedzialnosci,
- `persistence` nie zawiera fake’ow ani workerow,
- `application` rozroznia bus, execution context i integration contracts,
- platforma nie zawiera nieuzasadnionych typow biznesowych,
- wszystkie importy zostaly zaktualizowane,
- testy architektury, platformy i integracji przechodza,
- dokumentacja platformy opisuje nowa topologie,
- nie pozostaly nieuzywane stare katalogi ani kompatybilnosciowe re-eksporty.
