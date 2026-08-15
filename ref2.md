# Plan domkniecia enterprise Inbox/Outbox

## 1. Cel, ktory chcemy osiagnac

Celem jest doprowadzenie platformy delivery SHELL do stanu, w ktorym kazdy bounded context moze bezpiecznie odbierac i przetwarzac wlasne eventy, message oraz commandy w osobnym procesie i osobnej bazie danych.

Docelowy przeplyw:

```text
BC A lokalna transakcja
  -> outbox BC A
  -> relay / CDC / broker
  -> consumer BC B
  -> inbox BC B
  -> claim z lease
  -> lokalny processor BC B
  -> deserializacja kontraktu
  -> lokalny handler
  -> lokalna zmiana + outbox BC B + ack inboxa
  -> commit
```

### 1.1. Wymagania funkcjonalne

1. Kazdy BC czyta wylacznie swoj inbox.
2. Inbox ma jawny cykl zycia:

```text
PENDING -> PROCESSING -> PROCESSED
                    -> RETRY -> PROCESSING
                    -> DEAD_LETTER
```

`LEGACY_REVIEW` jest dozwolone tylko podczas migracji danych i musi zostac wyzerowane przed uruchomieniem nowego procesora.

3. Procesor dziala w semantyce at-least-once. Ponowne dostarczenie jest mozliwe i nie moze powodowac niekontrolowanych efektow ubocznych.
4. Claim rekordu jest krotka transakcja, a handler nie jest wykonywany pod dluga blokada SQL.
5. Lease pozwala odzyskac rekord po awarii workera.
6. Handler, lokalny outbox i potwierdzenie inboxa sa atomowe, jezeli korzystaja z tego samego UoW.
7. Jezeli atomowosc nie jest mozliwa, system uzywa `processed_delivery` jako jawnego mechanizmu deduplikacji.
8. Retry ma limit, backoff, jitter i rozroznia bledy chwilowe od bledow kontraktu.
9. DLQ zachowuje payload, typ, przyczyne, liczbe prob i czas niepowodzenia.
10. Replay nie moze konkurowac z aktywnym workerem posiadajacym wazny lease.
11. Kontrakty sa jawne, wersjonowane i nie wystawiaja automatycznie lokalnych klas command jako publicznego API.
12. Worker przezywa chwilowa awarie bazy, obsluguje shutdown i ma stabilny `worker_id`.
13. System ma metryki backlogu, retry, DLQ, lease expiration i czasu obslugi.
14. Gotowosc jest weryfikowana testami SQLite, PostgreSQL, brokerowymi oraz testem systemowym dwoch niezaleznych BC.

### 1.2. Wymagania niefunkcjonalne

- wspolna implementacja techniczna pozostaje w `shell/platform`;
- bounded contexts dostarczaja tylko modele, registry, bus, handlery i konfiguracje;
- domena nie zalezy od konkretnego brokera;
- transport moze byc zmieniony przez adapter `DeliveryTransport`;
- dane nie sa tracone podczas migracji ani restartu workera;
- nie zakladamy exactly-once na poziomie calego systemu;
- idempotencja jest obowiazkiem procesora i handlera.

## 2. Stan obecny i potwierdzone elementy

Ponizsze elementy istnieja w repozytorium i maja testy lub implementacje:

- `InboxStatus` z `PENDING`, `PROCESSING`, `PROCESSED`, `RETRY`, `DEAD_LETTER`, `LEGACY_REVIEW`;
- `InboxStateMixin` z polami lease, retry, status i schema version;
- indeksy inboxa;
- `InboxClaimService` z obsluga wygaslego lease;
- wspolny `InboxProcessorBase` dla event/message/command;
- `InboxBatchResult`;
- warunkowy acknowledge po `id` i `claimed_by`;
- exponential backoff z opcjonalnym jitterem;
- walidacja envelope i `UNSUPPORTED_SCHEMA_VERSION`;
- `InboxReplayService`;
- katalogi kontraktow per BC;
- adapter `DeliveryTransport` i adapter RabbitMQ;
- testy systemowe SQLite;
- testy claim service, procesorow, replay oraz workera;
- metryki backlogu w `InboxMetricsService`;
- testy architektury przechodza.

To nie oznacza jeszcze pelnej gotowosci produkcyjnej. Ponizsze braki musza zostac zamkniete.

## 3. Braki do usuniecia

### 3.1. Krytyczne braki poprawnosci

#### A. Atomowosc handler + outbox + inbox ack

Pliki do zweryfikowania i zmiany:

- `shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py`;
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`;
- `shell/platform/application/bus/event_bus.py`;
- kontenery BC i ich fabryki UoW.

Obecny processor wykonuje dispatch, a nastepnie ack przez osobna sesje. Nie dowodzi to, ze zmiana domeny, outbox i ack inboxa sa jednym commitem.

Ryzyko:

```text
handler commit
proces umiera przed ack
event zostaje wykonany ponownie
powstaje drugi outbox albo drugi audit
```

#### B. Brak `processed_delivery`

W repozytorium nie ma jawnej tabeli deduplikacji. Musi powstac jako fallback dla handlerow, ktore nie moga wspoldzielic sesji procesora, oraz dla efektow wymagajacych audytowalnego replay.

#### C. Brak heartbeat lease

Claim ustawia lease, ale dlugi batch moze przekroczyc jego czas. Bez heartbeat drugi worker moze przejac rekord, gdy pierwszy nadal wykonuje handler.

#### D. Migracje legacy

Baseline tworzy aktualne tabele, ale potrzebna jest migracja danych istniejacych tabel:

- `processed_at IS NULL` i ponizej limitu retry -> `PENDING`;
- rekord bez `processed_at` i po limicie retry -> `DEAD_LETTER`;
- rekord z `processed_at` bez oznak trwalego bledu -> `PROCESSED`;
- przypadek niesklasyfikowany -> `LEGACY_REVIEW`;
- po kroku operacyjnym liczba `LEGACY_REVIEW` musi wynosic zero.

#### E. Brak pelnej walidacji produkcyjnej

Testy RabbitMQ i PostgreSQL sa pomijane, gdy uslugi nie sa uruchomione. Nie wolno uznac planu za gotowy bez wykonania tych testow w CI lub srodowisku testowym.

### 3.2. Braki produkcyjne

- brak osobnego endpointu `/readiness`;
- brak pelnego healthchecku bazy, migracji, workera i backlogu;
- worker musi otrzymywac stabilny `worker_id` z konfiguracji;
- metryki musza byc dostarczane do wybranego backendu przed produkcja;
- brak testu timeoutu relay, bledu docelowej bazy i ponowienia;
- brak polityki cleanup/retencji dla `processed_delivery`;
- brak formalnej polityki replay aktywnego rekordu `PROCESSING` poza testem;
- kontrakt katalogu musi byc jawna allowlista, a nie tylko widokiem registry.

### 3.3. Braki testowe

Brakuje lub wymagaja uzupelnienia:

- crash pomiedzy handlerem a ackiem;
- podwojny outbox i podwojny audit po ponowieniu;
- wygasniecie lease podczas dlugiego batcha;
- heartbeat i utrata heartbeat;
- dryf zegara procesu;
- concurrency na PostgreSQL z `SKIP LOCKED`;
- replay aktywnego rekordu;
- upgrade/restore migracji bez utraty payloadu;
- event starszej wspieranej wersji przez upcaster;
- event nowszej wersji do DLQ;
- izolacja `correlation_id` i `causation_id` przy concurrency;
- pelny przeplyw RabbitMQ z dwoma niezaleznymi bazami.

## 4. Decyzje architektoniczne

### 4.1. Transakcja i deduplikacja

Obowiazuje hierarchia:

1. Najpierw claim transaction: rekord otrzymuje `PROCESSING`, `claimed_by` i `lease_until`, po czym transakcja jest commitowana.
2. Nastepnie processing transaction: handler, lokalny outbox i ack inboxa sa w jednym UoW.
3. Jezeli handler nie moze korzystac z tego samego UoW, obowiazkowe jest `processed_delivery`.
4. Nie dopuszczamy implementacji, w ktorej ack jest osobna operacja bez atomowosci i bez deduplikacji.

Zakres `session_scope` wynosi dokladnie jeden rekord i jeden processing UoW.
Jedna sesja SQLAlchemy nie moze byc wspoldzielona przez rownolegle taski.
Przy `max_concurrency > 1` kazdy rekord otrzymuje osobna sesje/UoW albo
procesor musi ograniczyc concurrency do `1`.

`processed_delivery` jest zapisywany w tej samej transakcji co efekt biznesowy
i outbox. Insert z konfliktem unikalnego klucza oznacza, ze delivery zostalo
juz wykonane i handler nie moze zostac uruchomiony ponownie. Nie wolno zapisac
samego `processed_delivery` przed efektem biznesowym w osobnej transakcji.

Semantyka `rollback()` wewnatrz deferred scope jest jednoznaczna: gdy handler
wykona `rollback()` w swoim UoW, procesor MUSI przerwac przetwarzanie rekordu
i zlecic retry — nie wolno mu dalej wykonywac ack ani commitowac sesji.
Rollback w deferred scope wygasza cala transakcje, wiec ewentualna zmiana
statusu inboxa musi pojsc warunkowo w nowej transakcji (jak `_schedule_failure`).

### 4.2. Batch i lease

Obowiazuje batch claim dla wydajnosci oraz heartbeat lease.

- batch ma limit rozmiaru i maksymalny czas;
- worker odnawia lease przed jego wygasnieciem;
- brak mozliwosci heartbeat oznacza batch jednoelementowy;
- handler musi byc idempotentny, bo lease nie zapewnia exactly-once;
- ack jest warunkowy po `id`, `status = PROCESSING` i `claimed_by`.

### 4.3. Wersjonowanie

- `schema_version` jest wersja payloadu;
- konsument obsluguje biezaca i poprzednia wersje przez upcaster;
- nowsza nieznana wersja trafia do DLQ z `UNSUPPORTED_SCHEMA_VERSION`;
- wersja envelope jest osobnym polem, jezeli zostanie wprowadzona;
- kontrakty sa katalogowane w `shell/<bc>/bootstrap/<bc>/contract_catalog.py`.

### 4.4. Kolejnosc

- brak gwarancji globalnej kolejnosci;
- `sequence_number` tylko dla kontraktow, ktore jawnie wymagaja kolejnosci per agregat;
- event z luka poprzednika trafia do oczekiwania/retry;
- event starszy od ostatniego zatwierdzonego jest konczony idempotentnie;
- kontrakty bez wymogu kolejnosci akceptuja out-of-order.

### 4.5. Migracje

Migracje sa forward-only. Rollback odbywa sie przez backup/restore albo migracje naprawcza. Downgrade nie jest wymagany, ale upgrade musi byc przetestowany na kopii danych.

## 5. Plan realizacji

### Faza 1 — Atomowosc handler + outbox + ack oraz `processed_delivery`

Rekomendowany wariant: **session-scope z odroczonym commitem** (two-phase UoW).
Procesor jest wlascicielem granicy transakcji; handler przezroczyscie dolacza
do tej samej sesji przez ambient scope (`ContextVar`) — ten sam idiom, ktorego
uzywa juz warstwa tracingu (`correlation_id_var` / `causation_id_var`).

Pliki:

- `shell/platform/application/context/` — nowy `session_scope_var` (ContextVar
  z aktywna sesja/session_factory oraz flaga `commit_on_exit`);
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py` —
  w `__aenter__`: jesli aktywny scope, uzyj sesji z scope i ustaw
  `deferred_commit=True`; w `__aexit__`/`commit`: przy deferred tylko flush,
  commit nalezy do procesora;
- `shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py` —
  wejsc w scope przed `_dispatch`, po dispatch zaktualizowac status
  `PROCESSED` w tej samej sesji i wykonac jeden commit; `_acknowledge` i
  `_schedule_failure` operuja na sesji z scope;
- nowy model `processed_delivery` (`consumer_name`, `delivery_id`,
  `processed_at`, unikalny `(consumer_name, delivery_id)`) jako fallback dla
  handlerow, ktore nie moga wspoldzielic sesji (np. inna baza);
- nowy port `DeliveryDedupStore` w platformie, zapis atomowy w UoW handlera;
- `shell/tests/system/test_transactional_semantics.py` — rozszerzenie o test
  crash po handlerze przed ackiem oraz brak drugiego outboxa i audytu.

Zasady:

1. Najpierw claim transaction (krotka transakcja, juz wdrozone).
2. Nastepnie processing transaction: handler + lokalny outbox + ack inboxa
   w jednym commicie przez session-scope.
3. Handler, ktory nie moze korzystac z sesji procesora, musi zapisac
   `processed_delivery` atomowo w swoim UoW; procesor konsultuje ja przed
   dispatch i nie uruchamia handlera ponownie.
4. Zakaz ack jako osobnej operacji bez atomowosci i bez deduplikacji.

Akceptacja:

- crash po handlerze przed ackiem NIE tworzy drugiego efektu biznesowego;
- sukces tworzy zmiane lokalna, outbox i `PROCESSED` atomowo;
- `processed_delivery` deduplikuje redelivery dla handlerow z osobna sesja.

### Faza 2 — Lease i heartbeat

Pliki:

- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py`;
- `shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py`;
- `shell/platform/infrastructure/messaging/polling_worker.py`.

Dzialania:

1. Dodac `renew_lease(record_id)` — warunkowy UPDATE `lease_until` gdzie
   `id + claimed_by + status = PROCESSING` oraz aktualny lease nie wygasl.
   Operacja musi sprawdzic `rowcount`; zero zmienionych rekordow oznacza utrate
   lease.
2. Odnawiac lease przed wygasnieciem w trakcie batcha; nieudane odnowienie
   zatrzymuje przetwarzanie rekordu, nie wykonuje ack i zleca retry po
   warunkowym zapisaniu stanu.
3. Ustalic `max_batch_time`; batch jednoelementowy przy braku heartbeat.
4. Dla SQLite bezpieczny tryb jednoelementowy; dla PostgreSQL test wielu
   workerow z `SKIP LOCKED`.

Heartbeat nie moze tylko przedluzac czasu lokalnie w pamieci. Musi wykonac
warunkowy UPDATE w bazie i potwierdzic, ze rekord nadal nalezy do tego workera.

Test dryfu zegara procesu (pozycja z 3.3) nalezy do tej fazy: claim i heartbeat
uzywaja zegara bazy (`CURRENT_TIMESTAMP`), wiec test symuluje maszynowy dryf
i weryfikuje, ze lease nie jest przedluzany/blokowany przez czas aplikacji.

Akceptacja:

- rekord z aktywnym lease nie jest przejmowany przez drugiego workera;
- wygasly lease nie powoduje utraty rekordu;
- worker odnawia lease przed jego wygasnieciem.

### Faza 3 — Readiness i metryki produkcyjne

Pliki:

- `shell/platform/framework/api/setup.py` — nowy endpoint `/readiness`;
- `shell/platform/infrastructure/messaging/inbox/inbox_metrics_service.py`;
- nowy port `MetricsBackend` i adapter (np. Prometheus) w infrastrukturze.

Dzialania:

1. `/readiness` sprawdza baze, stan migracji, aktywnosc workera (ostatni
   heartbeat) i prog backlogu z `InboxMetricsService`.
2. `/health` pozostaje liveness, `/readiness` to rzeczywista gotowosc.
3. Metryki backlogu, retry, DLQ, lease expiration, duration i duplicate
   delivery przez port/adaptor — platforma bez zaleznosci od backendu.

Akceptacja:

- readiness odpowiada poprawnie przy niedostepnej bazie i przepelnionym backlogu;
- metryki sa dostepne przed produkcja.

### Faza 4 — Upcaster i jawna allowlista kontraktow

Pliki:

- `shell/platform/infrastructure/serialization/event_deserializer.py` (oraz
  message/command analogicznie) — rejestr upcasterow
  `{type: {from_version: callable}}` obslugujacy `schema_version` z envelope;
- `shell/platform/application/contracts/contract_catalog.py` oraz katalogi BC —
  przejsc na jawny `build_contract_catalog` z wypelnionym
  `supported_schema_versions` i `retry_policy`;
- `shell/tests/architecture/test_contract_catalog.py`.

Dzialania:

1. Konsument obsluguje biezaca i poprzednia wersje przez upcaster.
2. Nowsza nieznana wersja trafia do DLQ z `UNSUPPORTED_SCHEMA_VERSION`.
3. Kazdy publiczny typ jest w katalogu; brak wpisu powoduje fail testu
   architektury.
4. Nie rejestrowac lokalnych commandow bez wpisu w katalogu.

Akceptacja:

- starszy wspierany schemat jest poprawnie upcastowany;
- nowszy nieznany schemat trafia do DLQ;
- katalog i registry maja ten sam zakres (test architektury).

### Faza 5 — Retencja i testy produkcyjne

Pliki:

- `shell/*/migrations/baseline.py` — migracje dla `processed_delivery` i kolumn
  dedup;
- `shell/tests/system/`, `shell/tests/platform/integration/sql_postgres/`,
  `shell/tests/platform/integration/sql_rabbit/`;
- `shell/docker-compose.test.yml`.

Dzialania:

1. Polityka retencji/cleanup dla DLQ i `processed_delivery` (konfigurowalne
   okno replay).
2. Test timeoutu relay i awarii docelowej bazy z ponowieniem.
3. Test upgrade/restore migracji bez utraty payloadu.
4. Pelny przeplyw RabbitMQ na dwoch niezaleznych bazach.
5. Uruchomic testy PostgreSQL i RabbitMQ w CI (nie pomijac gdy uslugi dzialaja).

Testy oznaczone jako `skipif` nie sa dowodem gotowosci. Pipeline produkcyjny
ma osobny job z uruchomionym PostgreSQL i RabbitMQ, a testy integration/system
musza tam zakonczyc sie wykonaniem, nie statusem skipped. Brak dostepnej uslugi
ma powodowac blad joba dla gate'a produkcyjnego.

Akceptacja:

- retencja jest testowana i konfigurowalna;
- przeplyw BC A outbox -> broker -> BC B inbox -> handler -> outbox przechodzi
  z sukcesem, retry, DLQ, duplikatem i restartem.

## 6. Kolejnosc wdrozenia

1. Faza 1 na jednym BC-pilocie (session): session-scope + atomowy ack +
   `processed_delivery` jako fallback.
2. Test crash po handlerze przed ackiem — brak drugiego outboxa i audytu.
3. Faza 2: heartbeat i stabilny `worker_id`.
4. Faza 3: `/readiness` i metryki przez port/adaptor.
5. Faza 4: upcaster i jawna allowlista kontraktow.
6. Faza 5: retencja i testy PostgreSQL/RabbitMQ w CI.
7. Rollout na pozostale BC po przejsciu testow SQLite i lokalnych systemowych.
8. Plan uznaje sie za zakonczony po akceptacji kryteriow z sekcji 7.

Nie wykonywac wszystkich faz jednoczesnie. Kazda faza musi zakonczyc sie testem
zakresowym przed przejsciem do nastepnej.

## 7. Kryteria koncowe

Plan uznaje sie za zrealizowany dopiero, gdy:

- wszystkie procesory event/message/command korzystaja ze wspolnego claim/process/ack;
- handler, outbox i ack sa atomowe albo zabezpieczone `processed_delivery`;
- lease jest odnawiany heartbeat i odzyskiwany po awarii;
- migracje legacy sa wykonane i `LEGACY_REVIEW = 0` przed startem workerow;
- `InboxBatchResult` jest uzywany przez processor i worker;
- retry, DLQ i replay maja testy oraz polityke retencji;
- kontrakty sa jawne, wersjonowane i testowane;
- `worker_id` jest stabilny;
- readiness sprawdza DB, migracje, workera i backlog;
- metryki sa dostepne przed produkcja;
- test SQLite, PostgreSQL i RabbitMQ przechodza;
- test systemowy dwoch niezaleznych baz potwierdza pelny przeplyw;
- ostrzezenia SQLAlchemy o ponownej rejestracji dynamicznych modeli sa wyjasnione lub usuniete;
- `pytest shell/tests/architecture -x` oraz odpowiednie testy platform/system przechodza bez pomijania krytycznych scenariuszy.

## 8. Zakres poza tym planem

Poza zakresem pozostaja:

- wybor konkretnego brokera jako decyzja biznesowa;
- zmiana domenowych aggregate i eventow niezwiązana z delivery;
- usuniecie wszystkich legacy API;
- obietnica exactly-once na poziomie calego systemu;
- automatyczne wystawianie wszystkich lokalnych commandow jako publicznych kontraktow.
