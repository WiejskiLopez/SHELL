# ResilientAsyncClient

## Status

Plan wdrożenia odpornego klienta HTTP dla komunikacji między mikroserwisami SHELL.

Pilot Execution został wdrożony: Definition i Session korzystają z klienta z
ograniczonym retry oraz circuit breakerem. Metryki, graceful degradation i
rozszerzenie na pozostałe adaptery są nadal kolejnymi etapami.

Dokument opisuje docelową zmianę architektoniczną. Implementacja obejmuje obecnie
mechanizm klienta i pilot Execution; nie obejmuje jeszcze pełnego zakresu
obserwowalności ani fallbacków biznesowych.

## Po co

Mikroserwis nie powinien traktować innego mikroserwisu jak lokalnej funkcji.
Wywołanie HTTP może zakończyć się:

- timeoutem;
- chwilową niedostępnością usługi;
- błędem DNS lub połączenia;
- odpowiedzią `429` albo `5xx`;
- powolnym działaniem zależności;
- serią błędów powodujących lawinę kolejnych prób.

Obecny `CorrelationIdAsyncClient` centralizuje przekazywanie `X-Correlation-ID`
i `X-API-Key`, ale nie kontroluje jeszcze zachowania przy awarii zależności.
Bez dodatkowej warstwy każdy adapter może implementować retry inaczej albo wcale,
a awaria jednego BC może zajmować zasoby workera i blokować przetwarzanie innych
żądań.

## Co to rozwiązuje

`ResilientAsyncClient` ma zapewnić wspólny techniczny mechanizm:

1. ograniczenia czasu połączenia i całego żądania;
2. retry wyłącznie dla operacji bezpiecznych lub jawnie idempotentnych;
3. exponential backoff z jitterem;
4. circuit breaker chroniący przed ciągłym wywoływaniem niedostępnej usługi;
5. propagację correlation ID i uwierzytelnienia usługi;
6. kontrolowane błędy domeny infrastrukturalnej zamiast przypadkowych wyjątków `httpx`;
7. metryki i logi bez ujawniania sekretów;
8. możliwość zdefiniowania graceful degradation przez konkretny adapter.

Mechanizm nie gwarantuje dostępności zależnej usługi. Ogranicza natomiast czas,
liczbę prób i wpływ jej awarii na usługę wywołującą.

## Gdzie to należy w architekturze

### `shell.platform`

Platforma dostarcza generyczny mechanizm techniczny:

- klient HTTP;
- konfigurację timeoutu i polityki retry;
- implementację circuit breakera;
- typowane wyjątki transportowe;
- hooki dla metryk i logowania;
- propagację correlation ID oraz nagłówka uwierzytelniającego.

Platforma nie zna `Definition`, `Session`, `Execution` ani żadnego DTO BC.

### `infrastructure` konkretnego mikroserwisu

Adapter należy do mikroserwisu konsumującego. To on określa:

- adres konkretnej usługi;
- operację i jej semantykę;
- czy operacja jest idempotentna;
- które kody błędów można ponawiać;
- czy istnieje fallback;
- jak odpowiedź HTTP mapuje się na lokalny kontrakt.

Przykład: `GraphDefinitionProviderHttpAdapter` może ponawiać bezpieczny odczyt
po błędzie połączenia, ale nie powinien automatycznie ponawiać komendy tworzącej
zasób bez idempotency key.

### `bootstrap`

Composition root składa klienta i adapter z konfiguracją środowiskową:

- `base_url`;
- klucz lub token usługi;
- timeout;
- polityka retry;
- parametry circuit breakera;
- nazwa zależności do metryk.

### deployment

Docker Compose, Kubernetes lub inny orchestrator odpowiada za:

- dostarczenie sekretów;
- readiness i liveness;
- limity CPU/pamięci;
- restart procesu;
- service discovery;
- rollout i rollback.

Nie przenosimy tych odpowiedzialności do klienta HTTP.

## Docelowy podział odpowiedzialności

```text
platform.infrastructure.http
    ResilientAsyncClient
    TimeoutPolicy
    RetryPolicy
    CircuitBreaker
    TransportError

service.infrastructure.adapters
    konkretny adapter HTTP
    semantyka operacji
    mapowanie odpowiedzi
    decyzja o fallbacku

service.bootstrap
    URL zależności
    sekret usługi
    konfiguracja polityki

Docker/Kubernetes/secret manager
    sekrety, sieć, limity, rollout, restart
```

## Proponowany kontrakt

Nazwa `ResilientAsyncClient` oznacza klienta, który zachowuje dotychczasowe
zachowanie `CorrelationIdAsyncClient` i dodaje odporność transportową.

Przykładowy kontrakt konfiguracyjny:

```python
ResilientAsyncClient(
    base_url="http://shell-definition-api:8002",
    service_api_key=definition_api_key,
    timeout=TimeoutPolicy(connect=1.0, read=3.0, write=3.0, pool=1.0),
    retry=RetryPolicy(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=1.0,
        retryable_methods=frozenset({"GET"}),
        retryable_statuses=frozenset({429, 502, 503, 504}),
    ),
    circuit_breaker=CircuitBreakerPolicy(
        failure_threshold=5,
        recovery_timeout=15.0,
    ),
)
```

Nazwy i typy mogą zostać dopasowane do istniejących konwencji. Istotne są
własności kontraktu:

- wartości domyślne nie mogą powodować nieskończonego czekania;
- retry musi być jawnie ograniczone;
- retry nie może obejmować wszystkich metod i wszystkich wyjątków;
- klucz usługi nie może być logowany;
- polityka musi być testowalna bez prawdziwej sieci;
- klient nie powinien ukrywać faktu, że zależność jest niedostępna.

## Zasady retry

Retry będzie dozwolone tylko dla:

- błędów połączenia i przejściowych timeoutów;
- odpowiedzi `429`, jeśli respektowanie `Retry-After` jest możliwe;
- odpowiedzi `502`, `503` i `504`;
- metod bezpiecznych, przede wszystkim `GET`.

Retry nie będzie domyślnie obejmować:

- `POST`, `PUT`, `PATCH` ani `DELETE`;
- błędów walidacji `4xx`;
- błędów autoryzacji `401` i `403`;
- błędów mapowania kontraktu;
- operacji, których idempotencja nie została potwierdzona.

Dla komend wymagających ponowienia potrzebny będzie osobny mechanizm
`idempotency_key` i jawny kontrakt odbiorcy. Sam retry transportowy nie rozwiązuje
problemów podwójnego wykonania komendy.

## Circuit breaker

Circuit breaker powinien mieć trzy stany:

```text
CLOSED -> OPEN -> HALF_OPEN -> CLOSED
                    |
                    +---- nieudana próba -> OPEN
```

- `CLOSED`: żądania są wysyłane normalnie;
- `OPEN`: żądania są odrzucane lokalnie do czasu recovery timeout;
- `HALF_OPEN`: przepuszczana jest ograniczona próba sprawdzająca;
- sukces zamyka obwód;
- porażka ponownie go otwiera.

Stan powinien być izolowany co najmniej per adres zależności, a docelowo per
usługa i operacja. Nie wolno dopuścić, aby awaria Definition blokowała wywołania
Session albo odwrotnie.

Circuit breaker nie powinien być globalnym singletonem dla wszystkich BC.
Jego cykl życia powinien należeć do klienta lub adaptera złożonego w composition
root konkretnej usługi.

## Graceful degradation

Fallback nie będzie implementowany w samym `ResilientAsyncClient`, ponieważ
platforma nie zna znaczenia danych. Fallback należy do adaptera lub warstwy
application konkretnego BC.

Dopuszczalne przykłady:

- odczyt opcjonalnych metadanych zwraca pusty wynik;
- cache zwraca ostatnią poprawną projekcję;
- proces odkłada zadanie do kolejki i kończy się kontrolowanym stanem;
- operacja krytyczna zwraca jawny błąd zależności.

Niedopuszczalne jest ciche zwracanie pustych danych dla wymaganej zależności,
jeśli mogłoby to doprowadzić do błędnej decyzji biznesowej.

## Zakres pierwszego wdrożenia

### W zakresie

- [x] rozszerzenie klienta platformowego o timeout;
- [x] typowane `RetryPolicy` i `CircuitBreakerPolicy`;
- [x] retry dla bezpiecznych odczytów adapterów Execution;
- [x] circuit breaker dla klienta zależności;
- zachowanie `X-Correlation-ID` i `X-API-Key`;
- testy jednostkowe z `httpx.MockTransport`;
- testy deterministycznego backoffu przez wstrzykiwany zegar/scheduler;
- metryki liczby prób, otwarć obwodu i odrzuceń lokalnych;
- dokumentacja konfiguracji i przykładowe wartości środowiskowe.

### Poza zakresem

- mTLS i service mesh;
- centralny gateway;
- cache rozproszony;
- automatyczne retry komend bez idempotency key;
- zmiany w logice domenowej;
- wspólny globalny circuit breaker dla wszystkich mikroserwisów;
- pełna polityka autoscalingu i rolloutów.

## Kolejność wprowadzenia

### Faza 0: kontrakt i inwentaryzacja

1. Sprawdzić wszystkie użycia `httpx.AsyncClient` i klientów platformowych.
2. Określić dla każdego adaptera metodę, idempotencję, timeout i dopuszczalne błędy.
3. Wybrać pierwszy pilot: odczyty Execution do Definition i Session.
4. Zdefiniować nazwy metryk i typy wyjątków.

### Faza 1: mechanizm platformowy

1. [x] Dodać polityki timeoutu, retry i circuit breakera w `platform.infrastructure`.
2. [x] Rozszerzyć `CorrelationIdAsyncClient` albo zastąpić go kompatybilnym
   `ResilientAsyncClient` bez zmiany portów domenowych.
3. Zapewnić propagację nagłówków oraz brak logowania sekretów.
4. Dodać limity ochronne: maksymalna liczba prób, maksymalny delay i timeout.

### Faza 2: pilot Execution

1. [x] Złożyć klientów Definition i Session w `ExecutionCoreContainer`.
2. Przekazać osobne polityki dla obu zależności.
3. [x] Włączyć retry wyłącznie dla odczytów.
4. Zmapować timeout, circuit open i błędy HTTP na lokalne błędy adaptera.
5. Dodać kontrolowany fallback tylko tam, gdzie kontrakt Execution go dopuszcza.

### Faza 3: testy awarii

1. Timeout połączenia i timeout odczytu.
2. [x] Jednorazowy błąd `503`, po którym retry kończy się sukcesem.
3. [x] Trwałe `503`, po którym obwód przechodzi do `OPEN`.
4. Odrzucenie żądania przez otwarty obwód bez wywołania sieci.
5. Powrót zależności i przejście `HALF_OPEN -> CLOSED`.
6. Brak retry dla `POST` i błędów `401/403/422`.
7. Zachowanie correlation ID oraz klucza usługi w każdym podejściu.
8. Brak ujawnienia sekretu w logu i wyjątku.

### Faza 4: rozszerzenie na pozostałe adaptery

Po przejściu pilota każda usługa dostaje własne polityki dla własnych zależności.
Nie należy automatycznie włączać tej samej liczby prób i timeoutu we wszystkich
BC.

## Pliki przewidziane do zmiany

Pierwszy pilot prawdopodobnie obejmie:

- `shell/platform/infrastructure/context/client.py`;
- nowy moduł polityk HTTP w `shell/platform/infrastructure/http/`;
- `shell/execution_service/infrastructure/.../graph_definition_provider_http_adapter.py`;
- `shell/execution_service/infrastructure/.../session_query_provider_http_adapter.py`;
- `shell/execution_service/bootstrap/execution/container/execution_core_container.py`;
- `shell/execution_service/bootstrap/execution/main.py`;
- `shell/execution_service/docker/docker-compose.yml`;
- testy platformy i Execution.

Nie powinny zmienić się:

- porty domenowe;
- agregaty i reguły domenowe;
- DTO kontraktów publicznych;
- modele persistence niezwiązane z komunikacją;
- kod innych BC, jeśli nie jest potrzebny do konfiguracji odbiorcy.

## Konfiguracja

Konfiguracja powinna być namespaced per zależność, na przykład:

```text
DEFINITION_SERVICE_URL
DEFINITION_SERVICE_API_KEY
DEFINITION_SERVICE_HTTP_CONNECT_TIMEOUT
DEFINITION_SERVICE_HTTP_READ_TIMEOUT
DEFINITION_SERVICE_HTTP_MAX_ATTEMPTS
DEFINITION_SERVICE_HTTP_CIRCUIT_FAILURE_THRESHOLD
DEFINITION_SERVICE_HTTP_CIRCUIT_RECOVERY_SECONDS

SESSION_SERVICE_URL
SESSION_SERVICE_API_KEY
SESSION_SERVICE_HTTP_CONNECT_TIMEOUT
SESSION_SERVICE_HTTP_READ_TIMEOUT
SESSION_SERVICE_HTTP_MAX_ATTEMPTS
SESSION_SERVICE_HTTP_CIRCUIT_FAILURE_THRESHOLD
SESSION_SERVICE_HTTP_CIRCUIT_RECOVERY_SECONDS
```

Wartości muszą być walidowane podczas startu. Timeouty i liczby prób mogą mieć
bezpieczne ograniczone wartości domyślne, ale URL-e i sekrety produkcyjne muszą
pochodzić z konfiguracji środowiska lub secret managera.

## Obserwowalność

Minimalne metryki:

- `http_client_requests_total{dependency,method,status}`;
- `http_client_attempts_total{dependency,method}`;
- `http_client_request_duration_seconds{dependency,method}`;
- `http_client_circuit_state{dependency}`;
- `http_client_circuit_rejections_total{dependency}`;
- `http_client_retries_total{dependency,reason}`.

Logi powinny zawierać nazwę zależności, metodę, status, numer próby i czas,
ale nie URL z sekretami, nagłówki uwierzytelniające ani payload zawierający dane
wrażliwe. `correlation_id` powinien być dostępny w kontekście logowania.

## Kryteria akceptacji

Etap uznajemy za wykonany, gdy:

- klient ma ograniczony timeout dla każdego żądania;
- retry jest ograniczone, deterministyczne w testach i obejmuje tylko dozwolone
  operacje;
- circuit breaker odcina niedostępną zależność;
- obwód może się zamknąć po odzyskaniu zależności;
- adaptery Execution używają klientów złożonych przez DI;
- sekrety i correlation ID są przekazywane w każdym dozwolonym podejściu;
- testy potwierdzają brak retry dla operacji nieidempotentnych;
- awaria zależności nie powoduje nieskończonego oczekiwania ani lawiny prób;
- pełne testy architektury, testy platformy i testy Execution przechodzą;
- dokumentacja konfiguracji opisuje wartości produkcyjne i testowe osobno.

## Ryzyka i decyzje

### Retry może powielić operację

Dlatego domyślnie obejmujemy tylko bezpieczne odczyty. Komendy wymagają
idempotency key albo jawnej polityki właściciela kontraktu.

### Circuit breaker może ukryć awarię

Dlatego każde lokalne odrzucenie musi być mierzalne i mapowane na jawny błąd,
a nie na przypadkowy pusty wynik.

### Jedna polityka dla wszystkich usług może być błędna

Dlatego mechanizm jest wspólny, ale wartości polityki należą do konkretnego
adaptera i zależności.

### Retry może zwiększyć obciążenie

Backoff, jitter, maksymalny delay, limit prób i circuit breaker są obowiązkowe.

### Klient HTTP może stać się zbyt szeroką abstrakcją

Nie powinien znać domeny, DTO, fallbacków ani workflowów. Jego API ogranicza się
do transportu i technicznych sygnałów odporności.

## Stan po wdrożeniu

Po pierwszej implementacji należy zaktualizować [2.md](2.md) tylko o faktycznie
wykonane punkty. Samo dodanie klasy klienta nie oznacza jeszcze spełnienia
wymagań dotyczących timeoutu, retry, circuit breakera i graceful degradation.
