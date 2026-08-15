# Audyt brakow planu `ref2.md`

Data audytu: 2026-08-15

## Wniosek

Plan z `ref2.md` nie jest jeszcze w calosci wykonany. Implementacja SQLite i podstawowy lifecycle inbox/outbox sa w duzej mierze gotowe, ale pozostaja luki w atomowej deduplikacji, uruchomieniu migracji legacy, konfiguracji produkcyjnej, readiness, testach awarii oraz automatycznej walidacji PostgreSQL/RabbitMQ.

## Wykonane czesciowo albo niezgodnie z planem

### 1. Atomowosc i `processed_delivery`

- `processed_delivery` istnieje jako model, ma unikalny klucz `(consumer_name, delivery_id)` i jest uwzglednione w baseline'ach.
- Procesor konsultuje ten store przez `is_duplicate`, ale nie zapisuje wpisu automatycznie. Wpis musi zapisac handler, a test deduplikacji (`test_inbox_atomicity.py`) przygotowuje rekord wczesniej zamiast potwierdzac pelny scenariusz: efekt biznesowy + outbox + `processed_delivery` w jednym UoW.
- Brakuje dowodu testowego crashu po wykonaniu handlera przed ackiem, w ktorym ponowienie nie tworzy drugiego efektu biznesowego, drugiego outboxa ani drugiego audytu. Istniejacy test crash (`test_event_inbox_processor_refactored.py`) dowodzi jedynie ponownego uruchomienia handlera (semantyka at-least-once), nie braku efektu ubocznego.
- Brakuje wyraznego, egzekwowanego portu `DeliveryDedupStore` w `application/ports/`. Obecna `ProcessedDeliveryStore` jest konkretna klasa w `infrastructure/messaging/inbox/`, a nie portem wymuszanym dla wszystkich handlerow, ktore nie dziela sesji procesora.

### 2. Lease, heartbeat i worker

- Heartbeat jest zaimplementowany, ale domyslny `heartbeat_interval_seconds` wynosi `0.0` i **nie jest podpiety w kontenerach produkcyjnych** (np. `session_core_container.py` nie przekazuje ani `heartbeat_interval_seconds`, ani `max_batch_time_seconds`). W produkcji lease nie jest odnawiany podczas dlugich batchy, a `max_batch_time` jest nieograniczony.
- Blad bazy podczas odnowienia lease jest traktowany jako "lease nadal posiadany" (`inbox_processor_base.py`, `_renew_lease` zwraca `True` przy wyjatku). To nie spelnia wymogu, aby utrata mozliwosci heartbeat zatrzymywala przetwarzanie i blokowala ack.
- Brakuje testow: wygasniecia lease podczas dlugiego handlera **bez heartbeat**, utraty heartbeat oraz dryfu zegara procesu. Test konkurencji na PostgreSQL z `SKIP LOCKED` **istnieje** (`test_pg_inbox_claim_concurrency.py`), ale nie jest wykonywany w CI (patrz sekcja walidacji).
- `worker_id` nie jest stabilny w produkcji: procesor bez konfiguracji generuje losowy `inbox-worker-{uuid}`. Co wiecej, `PollingWorkerConfig.worker_id` ustawiane w `main.py` BC (np. `"session-event-processor"`) jest **martwe** — `PollingWorker` nie przekazuje go do procesora, a fabryki procesorow w kontenerach nie ustawiaja `worker_id`.

### 3. Migracje legacy

- `InboxLegacyMigration` istnieje i klasyfikuje rekordy, ale nie jest automatycznie uruchamiana i weryfikowana przed startem workera.
- Nie ma operacyjnego guardraila wymuszajacego `LEGACY_REVIEW = 0` przed uruchomieniem nowego procesora.
- Brakuje testu upgrade/restore na kopii istniejacej bazy z potwierdzeniem zachowania payloadu.

### 4. Readiness i metryki produkcyjne

- Endpoint `/readiness` jest podlaczony tylko do aplikacji Session (`session/framework/session/api/app.py`); dla pozostalych samodzielnych BC nie jest podpiety ani testowany.
- Probe readiness (`sql_readiness_probe.py`) wnioskuje o aktywnosci workera wyłącznie z liczby rekordow `PROCESSING` z waznym lease; pusty backlog i brak jakiegokolwiek workera daje `ready = true`. Nie ma potwierdzenia aktywnosci przez ostatni heartbeat.
- Metryki maja usluge i port `MetricsBackend`, ale brak potwierdzonego produkcyjnego adaptera do wybranego backendu, np. Prometheus.
- Testy readiness istnieja dla niedostepnej bazy i przekroczonego backlogu; brakuje testow dla niegotowych migracji oraz nieaktywnego workera.

### 5. Wersjonowanie i kontrakty

- Upcaster i obsluga nieznanej wersji istnieja (test DLQ dla nowszej wersji w `test_event_inbox_processor_refactored.py`, testy jednostkowe upcastera). Brakuje kompletnego testu procesorowego obejmujacego jednoczesnie starszy wspierany event przez upcaster oraz nowszy event skierowany do DLQ.
- Allowlista katalogu kontraktow jest egzekwowana **tylko dla eventow** i tylko jako zgodnosc `catalog.names() == registry`. Nie jest egzekwowana dla publicznych message/command.
- `supported_schema_versions` i `retry_policy` z katalogu nie sa podpiete do `EnvelopeValidationPolicy` ani upcasterow w kontenerach produkcyjnych.

### 6. Replay, retencja i niezawodnosc transportu

- Replay ma implementacje i testy, w tym **test aktywnego rekordu `PROCESSING` z waznym lease** (`test_inbox_replay_service.py::test_does_not_replay_active_lease`): zwraca `False` i nie modyfikuje rekordu. Zakres do domkniecia to jednoznaczne odrzucenie konkurujacych replay wywolanych rownolegle (race), a nie sam pojedynczy przypadek.
- Retencja DLQ i `processed_delivery` jest zaimplementowana lokalnie i testowana, ale brak potwierdzenia uruchamiania cleanupu jako zaplanowanego procesu produkcyjnego.
- Ponowienie po awarii transportu jest testowane (`test_outbox_to_transport_relay.py`: nieoznaczony `published_at` -> redelivery). Brakuje testow timeoutu relay oraz awarii docelowej bazy w `EventOutboxToInboxRelay`.

## Niewykonana lub nieskuteczna walidacja produkcyjna

- **Niedopasowanie zmiennych srodowiskowych powoduje, ze testy PostgreSQL sa pomijane w CI.** Testy w `test_pg_inbox_claim_concurrency.py` i `test_pg_unit_of_work_rollback.py` pomijaja przez `skipif` na **`PG_TEST_URL`**, a job `production-gate` w `.github/workflows/ci.yml` ustawia **`POSTGRES_TEST_URL`**. Efekt: gate "przechodzi" cicho, a testy PG nie zostaja wykonane (skipped nie failuje joba).
- Testy RabbitMQ pomijaja przez `skipif` na `RABBIT_TEST_URL`; CI ja ustawia, wiec sa wykonywane, ale nie zostaly potwierdzone uruchomieniem lokalnie.
- Pelny przeplyw User BC -> osobna baza -> RabbitMQ -> Session BC -> osobna baza **ma test happy-path** (`test_microservice_flow.py`), ale nie jest w nim objety zestaw retry + DLQ + duplikat + restart workera w jednym scenariuszu dwoch BC.
- CI gate dla PostgreSQL i RabbitMQ **istnieje** (`production-gate` startuje uslugi i failuje, gdy nie wstana), ale jest nieskuteczny dla PG z powodu niedopasowania zmiennych; brak uslugi nie powoduje bledu joba dla testow pominietych.
- Izolacja `correlation_id` przy concurrency jest testowana (`test_concurrent_records_keep_isolated_context`); izolacja `causation_id` nie — test uzywa tej samej wartosci `"cause"` dla obu rekordow.
- **Testy SQLite (`shell/tests/platform/integration/sql_sqlite`) nie sa uruchamiane w CI ani w `run_tests.ps1`.** CI odpala tylko `platform/unit`, `sql_postgres`, `sql_rabbit` i `system`; `run_tests.ps1` odpala integracje tylko przy `PG_TEST_URL`. Atomicity, heartbeat, claim, legacy migration, readiness, retention, replay i relay nie maja automatycznej weryfikacji.
- Ostrzezenia SQLAlchemy o ponownej rejestracji dynamicznych modeli nie zostaly zweryfikowane pod katem wystepowania/wyjasnienia (wymaga uruchomienia testow z wywolaniami wielu BC w jednym procesie).

## Kryterium zakonczenia

Na podstawie powyzszych punktow planu z `ref2.md` nie nalezy jeszcze oznaczac jako zakonczonego. Najpierw trzeba domknac co najmniej: produkcyjny start po migracji legacy, wymuszony heartbeat i stabilny `worker_id`, pelna deduplikacje/test crash recovery, readiness workera, dopiecie testow SQLite/PG/RabbitMQ do CI bez statusu `skipped` oraz pelny test dwoch niezaleznych BC i baz obejmujacy retry, DLQ, duplikat i restart.
