# Plan poprawy i refaktoryzacji na podstawie `ref3.md`

Data: 2026-08-15

## 1. Cel planu

Celem jest doprowadzenie platformy Inbox/Outbox SHELL do stanu, w ktorym kazdy bounded context moze bezpiecznie odbierac i przetwarzac eventy, message oraz commandy w osobnym procesie i osobnej bazie danych.

Docelowy przeplyw:

```text
BC A transakcja lokalna
  -> outbox BC A
  -> relay / broker
  -> inbox BC B
  -> claim z lease
  -> handler BC B
  -> lokalna zmiana + outbox BC B + ack inboxa
  -> jeden commit
```

Plan ma usunac ryzyko podwojnych efektow po redelivery, utraty rekordu po awarii workera, uruchomienia workera przed migracja oraz falszywie zielonego CI. Refaktoryzacja ma pozostac wspolna w `shell/platform`, a bounded contexty maja dostarczac tylko swoje modele, registry, handlery i konfiguracje.

## 2. Zasady realizacji

1. Najpierw poprawiamy poprawnosc transakcyjna, potem konfiguracje i obserwowalnosc, a na koncu rozszerzamy walidacje produkcyjna.
2. Kazdy krok konczy sie testem zakresowym przed rozpoczeciem kolejnego.
3. Nie uznajemy testu oznaczonego jako `skipped` za dowod gotowosci produkcyjnej.
4. Claim jest krotka transakcja. Handler nie dziala pod blokada SQL claimu.
5. Handler, lokalny outbox i ack inboxa korzystaja z jednego UoW, gdy jest to mozliwe.
6. Gdy wspolny UoW nie jest mozliwy, obowiazkowa jest jawna deduplikacja `processed_delivery`.
7. Zmiany wykonujemy etapami i zachowujemy kompatybilnosc z aktualnym API oraz schematem danych.

## 3. Kolejnosc refaktoryzacji

### Krok 0 - Ustalenie punktu wyjscia i testow bazowych

**Co poprawic**

- Ustalic jeden sposob uruchamiania testow lokalnych i CI.
- Rozdzielic testy SQLite, PostgreSQL, RabbitMQ, systemowe i architektury.
- Dodac raportowanie liczby testow wykonanych i pominietych.
- Zapisac aktualny wynik jako punkt odniesienia przed dalszymi zmianami.

**Co to poprawia**

Usuwa ryzyko, ze zmiana wyglada na poprawna tylko dlatego, ze krytyczne testy nie zostaly uruchomione.

**Zakres**

- `.github/workflows/ci.yml`;
- `run_tests.ps1`;
- konfiguracja markerow pytest;
- testy w `shell/tests/platform/integration/sql_sqlite`, `sql_postgres`, `sql_rabbit` i `system`.

**Kryterium akceptacji**

- CI uruchamia testy SQLite oraz testy z uruchomionym PostgreSQL i RabbitMQ.
- Brak wymaganej uslugi powoduje blad joba produkcyjnego, a nie ciche `skipped`.
- Raport CI pokazuje jawnie wykonane i pominiete testy.

### Krok 1 - Domkniecie atomowosci i deduplikacji

**Co poprawic**

- Zachowac session-scope dla jednego processing UoW.
- Dodac jawny port `DeliveryDedupStore` w warstwie aplikacji/platformy.
- Pozostawic implementacje SQL w infrastrukturze, ale wymusic jej podpiecie w handlerach korzystajacych z osobnej sesji lub bazy.
- Zapewnic atomowy zapis `processed_delivery` razem z efektem biznesowym i outboxem.
- Obsluzyc konflikt unikalnego klucza jako sygnal, ze delivery zostalo juz wykonane.
- Nie zapisywac samego wpisu dedup wczesniej, w osobnej transakcji.

**Pliki do zmiany lub weryfikacji**

- `shell/platform/application/ports/`;
- `shell/platform/infrastructure/messaging/inbox/processed_delivery_store.py`;
- `shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py`;
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`;
- kontenery BC i fabryki UoW;
- `shell/tests/platform/integration/sql_sqlite/test_inbox_atomicity.py`;
- `shell/tests/system/test_transactional_semantics.py`.

**Co to poprawia**

Eliminuje podwojny efekt biznesowy, drugi outbox lub drugi audit po crashu pomiedzy handlerem i ackiem.

**Kryterium akceptacji**

- Crash po efekcie handlera przed ackiem moze spowodowac redelivery, ale nie tworzy drugiego efektu.
- Sukces zapisuje zmiane domenowa, outbox, `processed_delivery` i `PROCESSED` atomowo, gdy wymagany jest dedup.
- Rollback handlera powoduje retry i nie wykonuje acku.

### Krok 2 - Naprawa heartbeat, lease i stabilnego workera

**Co poprawic**

- Ustawic jawny interwal heartbeat oraz `max_batch_time_seconds` w konfiguracji produkcyjnej.
- Przekazac `worker_id` z `PollingWorkerConfig` do procesora albo wprowadzic jeden wspolny obiekt konfiguracji zawierajacy oba elementy.
- Usunac generowanie losowego identyfikatora w sciezce produkcyjnej; UUID moze pozostac tylko jako bezpieczny fallback developerski.
- Przy bledzie odnowienia lease traktowac lease jako utracony, zatrzymac dalszy handler/ack i zlecic retry zgodnie z warunkowym zapisem.
- Zachowac zegar bazy dla claim i heartbeat.
- Przy braku heartbeat ograniczyc batch do jednego rekordu.

**Pliki do zmiany lub weryfikacji**

- `shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py`;
- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py`;
- `shell/platform/infrastructure/messaging/polling_worker.py`;
- `shell/*/bootstrap/*/container/*_core_container.py`;
- `shell/*/bootstrap/*/main.py`;
- `shell/tests/platform/integration/sql_sqlite/test_inbox_heartbeat.py`;
- `shell/tests/platform/integration/sql_postgres/test_pg_inbox_claim_concurrency.py`.

**Co to poprawia**

Zapobiega przejeciu rekordu przez drugiego workera podczas dlugiego handlera i pozwala odzyskac rekord po awarii pierwszego workera.

**Kryterium akceptacji**

- Worker odnawia lease warunkowym UPDATE i rozpoznaje utrate lease.
- Drugi worker nie przejmuje rekordu z waznym lease.
- `worker_id` w logach i bazie jest stabilny dla danego procesu/konfiguracji.
- Testy obejmuja heartbeat, jego utrate, wygasniecie lease i dryf zegara.

### Krok 3 - Bezpieczny start po migracji legacy

**Co poprawic**

- Uruchamiac `InboxLegacyMigration` przed uruchomieniem procesora/workera.
- Po klasyfikacji sprawdzac liczbe rekordow `LEGACY_REVIEW`.
- Zablokowac start workera, jezeli pozostaly niesklasyfikowane rekordy.
- Rozdzielic jednorazowa migracje danych od zwyklego baseline schematu.
- Dodac test upgrade/restore na kopii bazy z zachowaniem payloadu.

**Pliki do zmiany lub weryfikacji**

- `shell/platform/infrastructure/messaging/inbox/inbox_legacy_migration.py`;
- `shell/*/bootstrap/*/main.py`;
- `shell/*/migrations/baseline.py`;
- `shell/tests/platform/integration/sql_sqlite/test_inbox_legacy_migration.py`;
- nowy test upgrade/restore.

**Co to poprawia**

Usuwa ryzyko uruchomienia nowego procesora na rekordach o nieznanym statusie oraz utraty danych podczas przejscia ze starego schematu.

**Kryterium akceptacji**

- Worker nie startuje, gdy `LEGACY_REVIEW > 0`.
- Po migracji rekordy sa sklasyfikowane jako `PENDING`, `PROCESSED` albo `DEAD_LETTER`.
- Payload przed i po migracji jest identyczny.

### Krok 4 - Readiness i obserwowalnosc produkcyjna

**Co poprawic**

- Podpiac `/readiness` do kazdego samodzielnego BC, nie tylko do Session.
- Rozszerzyc probe o stan migracji, ostatni heartbeat workera, backlog i ewentualne `LEGACY_REVIEW`.
- Rozdzielic liveness `/health` od readiness `/readiness`.
- Dodac adapter backendu metryk, np. Prometheus, przez port `MetricsBackend`.
- Rejestrowac backlog, retry, DLQ, wygasniecia lease, czas obslugi i duplicate delivery.
- Zaplanowac uruchamianie cleanupu retencji jako zadania produkcyjnego.

**Pliki do zmiany lub weryfikacji**

- `shell/platform/framework/api/readiness.py`;
- `shell/platform/infrastructure/health/sql_readiness_probe.py`;
- `shell/platform/infrastructure/messaging/inbox/inbox_metrics_service.py`;
- `shell/platform/application/ports/readiness.py`;
- `shell/platform/application/ports/metrics.py`;
- wszystkie `shell/*/framework/*/api/app.py`;
- `shell/platform/infrastructure/messaging/inbox/delivery_retention_service.py`.

**Co to poprawia**

Eliminuje falszywie pozytywny readiness, poprawia reakcje orkiestratora i daje operacyjna widocznosc problemow z dostarczaniem.

**Kryterium akceptacji**

- Niedostepna baza, brak migracji, nieaktywny worker, backlog ponad limit lub `LEGACY_REVIEW > 0` daje HTTP 503.
- Prawidlowo dzialajacy BC z aktywnym workerem daje HTTP 200.
- Metryki sa dostepne w wybranym backendzie.

### Krok 5 - Jawne kontrakty i wersjonowanie

**Co poprawic**

- Rozszerzyc walidacje katalogu na publiczne eventy, message i commandy.
- Wymusic jawna allowliste: typ bez wpisu w katalogu nie moze zostac zarejestrowany jako publiczny kontrakt.
- Podpiac `supported_schema_versions` i `retry_policy` do walidacji envelope i procesorow.
- Dodac test starszej wspieranej wersji przez upcaster oraz nowszej wersji kierowanej do DLQ.
- Utrzymac osobne registry dla bounded contextow.

**Pliki do zmiany lub weryfikacji**

- `shell/platform/application/contracts/contract_catalog.py`;
- `shell/*/bootstrap/*/contract_catalog.py`;
- `shell/*/bootstrap/*/event_registry.py`;
- `shell/platform/infrastructure/serialization/upcaster.py`;
- deserializery event/message/command;
- `shell/tests/architecture/test_contract_catalog.py`;
- testy procesorow SQLite.

**Co to poprawia**

Chroni granice API, zapobiega przypadkowemu wystawieniu lokalnych commandow i pozwala bezpiecznie rozwijac payloady.

**Kryterium akceptacji**

- Nieznany typ lub nieobslugiwana wersja nie trafia do handlera.
- Starsza wspierana wersja jest upcastowana i przetworzona.
- Nowsza wersja konczy w DLQ z `UNSUPPORTED_SCHEMA_VERSION`.
- Test architektury wykrywa brak wpisu w katalogu.

### Krok 6 - Replay, retencja i odporność transportu

**Co poprawic**

- Dodac warunkowa aktualizacje replay, ktora atomowo sprawdza status i waznosc lease.
- Dodac test rownoleglych prob replay tego samego rekordu.
- Dodac test timeoutu relay oraz awarii docelowej bazy i ponowienia.
- Ustalac i konfigurowac okna retencji DLQ oraz `processed_delivery`.
- Uruchamiac cleanup jako kontrolowane zadanie z metrykami wyniku.

**Pliki do zmiany lub weryfikacji**

- `shell/platform/infrastructure/messaging/inbox/inbox_replay_service.py`;
- `shell/platform/infrastructure/messaging/inbox/delivery_retention_service.py`;
- adaptery relay/transport;
- `shell/tests/platform/integration/sql_sqlite/test_inbox_replay_service.py`;
- testy relay i systemowe.

**Co to poprawia**

Zapobiega kolizji operatora replay z aktywnym workerem i ogranicza niekontrolowany wzrost tabel delivery.

**Kryterium akceptacji**

- Rekord z waznym lease nie moze zostac zresetowany przez replay, takze przy rownoleglych wywolaniach.
- Timeout lub awaria bazy nie gubi outboxa i powoduje ponowienie.
- Retencja usuwa tylko rekordy starsze od konfigurowalnego okna.

### Krok 7 - Naprawa CI i pelna walidacja produkcyjna

**Co poprawic**

- Ujednolicic nazwe zmiennej PostgreSQL: `PG_TEST_URL` albo `POSTGRES_TEST_URL`, we wszystkich testach, skryptach i workflow.
- Dodac uruchamianie testow SQLite do CI.
- Wymusic `--strict-markers` i sprawdzanie, czy krytyczne testy nie sa pominiete.
- Dodac test pelnego przeplywu dwoch BC i dwoch baz: sukces, retry, DLQ, duplikat i restart workera.
- Dodac test izolacji `correlation_id` i `causation_id` z roznymi wartosciami dla rownoleglych rekordow.
- Uruchomic testy z wieloma BC w jednym procesie i usunac albo udokumentowac ostrzezenia SQLAlchemy o dynamicznych modelach.

**Pliki do zmiany lub weryfikacji**

- `.github/workflows/ci.yml`;
- `run_tests.ps1`;
- `shell/tests/*/conftest.py`;
- `shell/tests/system/`;
- `shell/tests/platform/integration/`.

**Co to poprawia**

Zapewnia, ze status CI rzeczywiscie oznacza przejscie scenariuszy produkcyjnych, a nie tylko przejscie testow jednostkowych lub pominiecie integracji.

**Kryterium akceptacji**

- PostgreSQL, RabbitMQ i SQLite sa wykonywane w odpowiednich jobach.
- Brak uslugi albo brak konfiguracji dla production gate konczy job bledem.
- Pelny przeplyw dwoch BC przechodzi z retry, DLQ, duplikatem i restartem.
- Brak niewyjasnionych warningow SQLAlchemy.

## 4. Kolejnosc wdrozenia i zaleznosci

1. Krok 0: testy bazowe i korekta CI.
2. Krok 1: atomowosc i `processed_delivery`.
3. Krok 2: heartbeat, lease i `worker_id`.
4. Krok 3: migracja legacy przed startem workera.
5. Krok 4: readiness i metryki.
6. Krok 5: kontrakty i wersjonowanie.
7. Krok 6: replay, retencja i odporność transportu.
8. Krok 7: finalna walidacja systemowa i zamkniecie kryteriow.

Krok 0 musi poprzedzac pozostale kroki, bo bez wiarygodnego CI nie da sie odroznic poprawy od pozornego przejscia. Kroki 1-3 sa krytyczne dla poprawnosci danych i powinny zostac wykonane przed wlaczeniem workerow produkcyjnych. Kroki 4-7 domykaja operacyjnosc i dowod gotowosci.

## 5. Definicja zakonczonej refaktoryzacji

Refaktoryzacje mozna uznac za zakonczona dopiero, gdy:

- kazdy processor event/message/command korzysta ze wspolnego claim/process/ack;
- efekt biznesowy, outbox i ack sa atomowe albo chronione przez `processed_delivery`;
- heartbeat, lease recovery i stabilny `worker_id` dzialaja w konfiguracji produkcyjnej;
- `LEGACY_REVIEW = 0` jest wymagane przed startem workera;
- readiness sprawdza baze, migracje, heartbeat workera, backlog i stan legacy;
- kontrakty sa jawne, wersjonowane i testowane;
- replay, retencja i transport maja testy awarii oraz retry;
- testy SQLite, PostgreSQL, RabbitMQ i system dwoch BC przechodza bez krytycznych `skipped`;
- CI nie maskuje braku uslug przez niedopasowane zmienne srodowiskowe;
- ostrzezenia dynamicznej rejestracji modeli SQLAlchemy sa usuniete albo udokumentowane i zaakceptowane.
