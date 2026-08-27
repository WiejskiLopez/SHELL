# Plan domknięcia separacji mikroserwisów

## Cel

Doprowadzić obecny podział kodu i artefaktów do stanu, w którym każdy bounded context może być niezależnie budowany, wdrażany, obserwowany, skalowany, aktualizowany i wycofywany.

Aktualny stan bazowy:

- istnieją osobne pakiety, lockfile'y, Dockerfile'y, migracje i entrypointy usług;
- istnieją per-service event registry oraz osobne modele `Base`;
- granice importów i izolacja artefaktów są sprawdzane automatycznie;
- podstawowe mechanizmy retry, circuit breaker, readiness, inbox/outbox i DLQ są dostępne;
- do domknięcia pozostają głównie operacyjność produkcyjna, testy awarii, publikacja wszystkich obrazów oraz spójność dokumentacji.

## Status wykonania

Legenda: `[x]` wykonane i potwierdzone testem lub kodem, `[~]` częściowe, `[ ]` planowane.

### Wykonane

- [x] Każdy z siedmiu bounded contexts ma własny pakiet, entrypoint, kontener, migracje, Dockerfile, compose i lockfile.
- [x] Każdy bounded context ma własny event registry; rejestry są sprawdzane testem izolacji.
- [x] Granice importów między bounded contexts oraz granice kontenerów są egzekwowane testami architektury.
- [x] Komunikacja między istniejącymi zależnościami BC używa adapterów HTTP zamiast bezpośrednich importów.
- [x] W profilu `prod` każdy entrypoint wymaga własnych zmiennych `*_SERVICE_DATABASE_URL`, `*_SERVICE_BROKER_URL` i `*_SERVICE_API_KEY`.
- [x] Wspólne zmienne `SHELL_*` nie są fallbackiem dla konfiguracji produkcyjnej usługi.
- [x] Brak wymaganej wartości produkcyjnej zatrzymuje konfigurację przed utworzeniem kontenera, migracją i startem serwera.
- [x] Profil `dev` zachowuje lokalne fallbacki i dotychczasowy sposób uruchamiania.
- [x] Testy konfiguracji, kontraktu niezależnych usług, izolacji event registry i testy architektury przechodzą.

### Częściowe lub niepotwierdzone

- [~] Niezależność artefaktów jest zabezpieczona testami i konfiguracją, ale pełny niezależny rollout produkcyjny wymaga jeszcze dowodów z pipeline'u i środowiska stagingowego.
- [~] Uwierzytelnianie service-to-service nadal opiera się na `X-API-Key`; wymiana na mTLS lub podpisane tokeny pozostaje zadaniem.
- [~] Obserwowalność, testy awarii, autoscaling, rollout/rollback i pełna publikacja artefaktów wymagają dalszej weryfikacji operacyjnej.

## Zasady realizacji

- każda usługa ma własny obraz, konfigurację, bazę, sekrety, pipeline i cykl release;
- `shell.platform` zawiera wyłącznie mechanizmy generyczne i nie zna kodu żadnego BC;
- komunikacja między usługami odbywa się wyłącznie przez wersjonowane kontrakty HTTP lub eventowe;
- zmiana jednego BC nie może wymuszać budowania ani wdrażania pozostałych;
- każda zmiana modelu, kontraktu lub konfiguracji musi mieć test i aktualizację dokumentacji;
- tryb monolityczny pozostaje narzędziem lokalnym, ale nie może być wymagany przez wdrożenie rozproszone.

# Etap 1: Produkcyjna niezależność i operacyjność

## 1. Ustabilizować kontrakty i wersjonowanie

- spisać katalog usług, właścicieli, endpointów, eventów, komend i zależności;
- nadać kontraktom niezależne wersje oraz jawne `schema_version`, `event_type`, `event_id`, `occurred_at`, `correlation_id` i `causation_id`;
- dodać testy kompatybilności aktualnej i poprzedniej wersji kontraktów;
- zdefiniować politykę semver platformy, breaking changes, deprecacji i okresu przejściowego;
- utworzyć changelog platformy i kontraktów;
- zapewnić, że registry każdej usługi ładuje wyłącznie własne eventy oraz jawnie wspierane kontrakty zewnętrzne.

**Odbiór:** kontrakt można zmienić i wdrożyć producenta bez jednoczesnego wdrażania konsumenta, a test kompatybilności wykrywa breaking change.

## 2. Domknąć bezpieczeństwo komunikacji i konfiguracji

- zastąpić sam klucz `X-API-Key` mechanizmem odpowiednim dla środowiska produkcyjnego: mTLS, podpisanymi tokenami albo równoważnym mechanizmem;
- ograniczyć uprawnienia kont baz danych, brokera i sekretów per usługa;
- rozdzielić konfigurację `dev`, `test`, `staging` i `prod`;
- wymusić brak fallbacków sekretów w profilu produkcyjnym;
- walidować przy starcie adres bazy, brokera, sekretów, timeoutów i identyfikatora usługi;
- dodać test uruchomienia każdej usługi z minimalnym własnym zestawem zmiennych środowiskowych;
- rozszerzyć testy negatywne o brak autoryzacji, błędny token, dostęp do obcego endpointu i niewystarczające uprawnienia.

**Odbiór:** usługa nie startuje z niepełną konfiguracją produkcyjną i nie może użyć sekretu należącego do innego BC.

## 3. Wzmocnić odporność i lifecycle

- uzupełnić klienta HTTP o bulkhead, limity współbieżności i graceful degradation;
- potwierdzić retry wyłącznie dla operacji bezpiecznych lub idempotentnych;
- stosować idempotency key dla komend, które mogą zostać powtórzone;
- zapewnić workerowi kontrolowany shutdown, heartbeat, lease, backoff, retry i DLQ;
- sprawdzić zachowanie po utracie bazy, brokera, zależności HTTP i po restarcie procesu;
- rozdzielić proces API i workerów tam, gdzie wymagają niezależnego skalowania;
- zdefiniować limity CPU/pamięci, readiness jako warunek przyjęcia ruchu oraz politykę rollout/rollback dla każdego obrazu;
- przygotować konfigurację autoscalingu według właściwych metryk: latency, error rate, backlog i DLQ.

**Odbiór:** awaria jednej zależności kończy się kontrolowanym błędem, retry nie tworzy lawiny, a wdrożenie można wycofać bez migracji pozostałych usług.

## 4. Włączyć obserwowalność produkcyjną

- emitować strukturalne logi z nazwą usługi, wersją obrazu, `correlation_id` i `causation_id`;
- zastąpić lub uzupełnić `LoggingMetricsBackend` rzeczywistym backendem metryk;
- mierzyć requesty, błędy, czas odpowiedzi, backlog, retry, lease expiry, duplikaty i DLQ;
- dodać tracing HTTP oraz przetwarzania eventów;
- zdefiniować SLI/SLO i alerty osobno dla każdej usługi;
- dodać dashboard pokazujący przepływ przez kilka usług i broker;
- nie logować sekretów, tokenów ani pełnych wrażliwych payloadów.

**Odbiór:** operator może prześledzić żądanie przez kilka usług i wskazać usługę lub zależność powodującą problem.

## 5. Rozszerzyć testy niezależnego wdrożenia

- uruchamiać co najmniej dwie usługi jako osobne procesy i komunikować je przez HTTP/broker;
- dodać testy kontraktowe HTTP i eventowe dla nazw, typów, wersji, metadanych i błędów;
- dodać scenariusze awarii: timeout HTTP, niedostępny broker, duplikat eventu, restart konsumenta, wygasły lease i DLQ;
- testować upgrade migracji na pustej bazie oraz reset/re-upgrade każdej usługi;
- testować, że zmiana obcego BC nie zmienia digestu obrazu usługi;
- dodać test pełnego composition root dla każdej usługi;
- utrzymać testy monolitu jako regresję lokalną, ale nie jako warunek niezależnego release'u.

**Odbiór:** wszystkie testy przechodzą w trybie izolowanym, rozproszonym oraz regresyjnym, a test awarii potwierdza kontrolowane odzyskanie systemu.

## 6. Publikować wszystkie artefakty

- ujednolicić workflow User, Session i pozostałych usług;
- każdy workflow ma wykonywać testy usługi, testy architektury, skan bezpieczeństwa, build wheel i build obrazu;
- wymagać czystego commita dla release'u;
- tagować obraz wersją usługi i SHA commita;
- publikować wszystkie obrazy i wheels do właściwego repozytorium artefaktów;
- generować release manifest zawierający wersje pakietów, digest obrazu, wersję platformy i commit;
- dodać automatyczną weryfikację niezmienności digestu po zmianie innego BC.

**Odbiór:** każda usługa ma powtarzalny release z identyfikowalnym obrazem i manifestem, bez ręcznego uruchamiania pozostałych pipeline'ów.

# Etap 2: Dokumentacja, CI/CD i formalne zamknięcie

## 1. Uaktualnić dokumentację architektury

- poprawić `2.md`, aby używał aktualnej topologii `shell/<service>_service/`;
- zastąpić nieaktualne odniesienia do `messaging_service` właściwym obecnym bounded contextem, czyli `ingestion_service`, albo jasno opisać zmianę nazwy;
- rozdzielić statusy: zrobione, częściowe, planowane i niewymagane dla bieżącego release'u;
- opisać zależności między usługami, właścicieli danych, kontrakty i wymagane sekrety;
- opisać osobno tryb lokalny, testowy, stagingowy i produkcyjny;
- dodać instrukcję budowania, migracji, uruchamiania API/workera, healthchecków i rollbacku.

## 2. Utworzyć dokument wdrożeniowy

Dokument wdrożeniowy powinien zawierać dla każdej usługi:

- nazwę pakietu, wersję, obraz i port;
- wymagane zmienne środowiskowe oraz źródło sekretów;
- własną bazę, migracje i komendę upgrade;
- zależności HTTP i brokerowe;
- endpointy `/health` i `/readiness`;
- komendy build, test, publish, deploy i rollback;
- limity zasobów, skalowanie i warunki gotowości;
- procedurę odtworzenia komunikacji po awarii.

## 3. Ujednolicić CI/CD

- wprowadzić wspólny reusable workflow z macierzą usług;
- uruchamiać pipeline tylko dla zmienionej usługi oraz wymaganej wersji platformy;
- dodać osobne joby: test, lint, typowanie, migracje, kontrakty, security, build, image scan i publish;
- wymusić `uv lock --check` oraz weryfikację granic artefaktu;
- publikować obraz dopiero po przejściu wszystkich kontroli;
- przechowywać release manifest jako artefakt pipeline'u;
- dodać ręczny etap zatwierdzenia wdrożenia produkcyjnego i automatyczny rollback.

## 4. Uporządkować kryteria jakości

- utrzymywać `pytest shell/tests/architecture -x` jako minimalny punkt kontrolny;
- dodać osobne zestawy `shell/tests/<service>`, `shell/tests/contracts` i `shell/tests/system`;
- definiować przy każdym nowym wymaganiu test odbiorowy;
- usuwać z dokumentacji checkboxy bez odpowiadającego im testu lub dowodu w pipeline;
- raportować jawnie testy pominięte z powodu braku infrastruktury, np. RabbitMQ;
- nie uruchamiać `deploy.ps1` jako zwykłej walidacji, ponieważ wykonuje także commit.

**Odbiór etapu 2:** dokumentacja opisuje rzeczywisty kod, każdy wymóg ma właściciela i test, a release usługi można odtworzyć z pipeline'u na podstawie manifestu.

# Kolejność realizacji

1. Katalog usług, kontrakty i polityka wersjonowania.
2. Konfiguracja produkcyjna, sekrety i uwierzytelnianie service-to-service.
3. Testy awarii i niezależnego uruchamiania.
4. Lifecycle workerów, limity zasobów, rollout i rollback.
5. Metryki, tracing, dashboardy i alerty.
6. Publikacja obrazów wszystkich usług oraz digest/release manifest.
7. Aktualizacja `2.md` i utworzenie dokumentacji wdrożeniowej.
8. Końcowy audyt wymagań i pełny pipeline bez ręcznych wyjątków.

# Warunek końcowy

Separację można uznać za zakończoną dopiero wtedy, gdy dla każdego z siedmiu aktualnych usług:

- niezależny build nie kopiuje kodu innych usług;
- istnieją własny pakiet, lockfile, obraz, wersja, pipeline i manifest;
- usługa ma własną bazę, migracje, konfigurację i sekrety;
- komunikacja z innymi usługami korzysta wyłącznie z wersjonowanych kontraktów;
- testy potwierdzają izolację, kompatybilność, awarie, idempotencję i rollback;
- operator ma logi, metryki, trace, readiness, dashboard i alerty;
- aktualizacja lub wycofanie jednej usługi nie wymaga wdrażania pozostałych;
- dokumentacja i statusy odpowiadają rzeczywistemu stanowi repozytorium.
