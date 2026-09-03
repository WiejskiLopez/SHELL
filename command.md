# Command Delivery w SHELL — docelowy model enterprise

Status: propozycja refaktoryzacji
Data analizy: 2026-08-31
Zakres: command bus, komendy synchroniczne, asynchroniczne command outbox/inbox, RabbitMQ i granice bounded contexts.

## 1. Decyzja architektoniczna

Command i event są różnymi kontraktami:

```text
Command = intencja wykonania operacji: "wykonaj X"
Event   = fakt po wykonaniu operacji: "X się wydarzyło"
```

`outbox` nie jest typem wiadomości. Jest trwałym buforem dostarczenia. Dlatego poprawne są osobne ścieżki:

```text
komenda lokalna:
Command -> CommandBus -> Handler -> Aggregate -> DomainEvent

komenda synchroniczna między BC:
Command -> SynchronousCommandPort -> HTTP/gRPC -> Handler -> Response

komenda asynchroniczna między BC:
Command -> AsyncCommandDispatcher -> CommandOutbox -> Relay -> Broker
        -> CommandInbox -> CommandInboxProcessor -> CommandBus -> Handler
```

### Decyzja dla SHELL

1. Nazwa komendy opisuje wyłącznie intencję biznesową.
2. Tryb dostarczenia wynika z użytego portu/dispatchera, nie z nazwy klasy komendy.
3. `CommandBus` pozostaje kanałem lokalnym i natychmiastowym.
4. Komunikacja między BC domyślnie używa synchronicznego portu HTTP/gRPC, jeżeli caller potrzebuje odpowiedzi.
5. Asynchroniczny command używa outboxa tylko wtedy, gdy operacja jest długa, może czekać na odbiorcę albo świadomie akceptujemy eventual consistency.
6. Event outbox i command outbox pozostają całkowicie rozdzielone.

## 2. Ocena stanu obecnego

### Jest poprawne

- Komendy BC są niemutowalnymi `dataclass(frozen=True, slots=True)`.
- `CommandBus` jest osobnym mechanizmem od event busa.
- `CommandDeliveryEnvelope` jest oddzielony od `IntegrationEventDeliveryEnvelope`.
- Wire routing rozróżnia `event.*` i `command.*`.
- `CommandInboxProcessor` deserializuje komendę i przekazuje ją do lokalnego `CommandBus`.
- Inbox ma lease, retry, DLQ, correlation ID i idempotencję.
- Modele delivery są budowane przez platformowe fabryki dla metadata konkretnego BC.
- Ack brokera następuje po trwałym zapisie do lokalnego inboxa.

### Wymaga uzupełnienia

1. `SqlCommandOutboxPublisher` zapisuje rekord i od razu wykonuje własny commit. Nie może być używany do komendy powstałej razem ze zmianą domeny, jeżeli chcemy atomowości efekt + command outbox.
2. `SqlCommandOutboxPublisher` nie jest nazwą idealną: klasa nie publikuje do brokera, tylko zapisuje rekord w SQL. To writer.
3. `CommandOutboxToTransportRelay` istnieje, ale produkcyjne kontenery mają obecnie widoczny wiring relaya eventowego; trzeba jawnie podłączyć również command relay i worker.
4. W produkcji nie ma znalezionego jawnego nadawcy komend przez `SqlCommandOutboxPublisher`; obecne testy dowodzą mechaniki, nie pełnego przepływu biznesowego.
5. Wszystkie kolejki commandów wiążą `command.#`. W efekcie każdy BC może otrzymać każdą komendę, także taką, której nie jest właścicielem.
6. Registry jest budowane z nazw klas Python (`CreateWorkflowCommand`). Nazwa klasy nie jest stabilnym kontraktem między usługami i może kolidować między BC.
7. `outbox_command` nie ma osobnego `schema_version`, `source_service`, `target_service` ani stabilnego `command_id` odrębnego od technicznego `outbox.id`.
8. Relay trzyma transakcję i `FOR UPDATE` podczas wywołania sieciowego brokera. Przy wolnym brokerze locki DB są utrzymywane zbyt długo.
9. Model outboxa nie ma stanu próby, `next_attempt_at` i ostatniego błędu. Retry jest obecnie głównie efektem ponownego znalezienia nieopublikowanego wiersza.
10. Obecne nazewnictwo `dispatched_at` jest niejednoznaczne. W momencie zapisu do outboxa komenda została wydana, ale jeszcze nie została dostarczona ani wykonana.

## 3. Docelowe nazwy

### Kontrakty biznesowe

Pozostawić obecny styl nazw operacji:

```text
CreateWorkflowCommand
ChangeWorkflowCommand
DeleteWorkflowCommand
OpenSessionCommand
```

Nie dodawać do nazw biznesowych `Async`, `Sync`, `Rabbit` ani `Outbox` tylko dlatego, że zmienia się transport.

Wyjątek: gdy zmienia się znaczenie biznesowe i kontrakt odpowiedzi:

```text
CreateWorkflowCommand          # wykonaj operację i zwróć wynik
RequestWorkflowCreationCommand # przyjmij żądanie do późniejszego wykonania
```

### Kanały i adaptery

| Obecna/naturalna odpowiedzialność | Docelowa nazwa | Warstwa |
|---|---|---|
| lokalne wykonanie | `CommandBus` | platform application |
| synchroniczny kontrakt z BC | `SynchronousCommandPort` albo konkretny `WorkflowCommandPort` | application/domain port |
| asynchroniczny kontrakt z BC | `AsyncCommandDispatcher` | application port |
| zapis SQL do outboxa | `SqlCommandOutboxWriter` | infrastructure |
| relay outbox→broker | `CommandOutboxRelay` | infrastructure |
| transport brokera | `CommandDeliveryTransport` | application port |
| adapter RabbitMQ | `RabbitCommandDeliveryTransport` | infrastructure |
| zapis broker→inbox | `RabbitCommandInboxConsumer` | infrastructure |
| lifecycle inboxa | `CommandInboxProcessor` | infrastructure/application adapter |
| registry kontraktów | `CommandContractRegistry` | bootstrap/application |

`CommandOutboxToTransportRelay` jest semantycznie poprawne, ale `CommandOutboxRelay` jest krótsze i nadal jednoznaczne po rozdzieleniu event relay. Zmiana jest opcjonalna i powinna być wykonana wyłącznie razem z aliasem migracyjnym.

### Rekomendowana granica API

```python
class AsyncCommandDispatcher(Protocol):
    async def dispatch(self, command: object, *, target_service: str) -> str: ...
```

Adapter SQL nie powinien być wywoływany bezpośrednio przez handler ani controller. Właściciel przypadku użycia korzysta z portu, a bootstrap składa:

```text
AsyncCommandDispatcher
  -> SqlCommandOutboxWriter
```

Dzięki temu nazwa transportu nie przecieka do application layer.

## 4. Stabilny kontrakt komendy

### Nazwa wire

Nie używać `__name__` klasy jako jedynego identyfikatora kontraktu. Wprowadzić jawne, namespacowane nazwy:

```text
execution.workflow.create
execution.workflow.change
execution.workflow.delete
scheduling.scheduler_job.create
session.session.open
```

Python może nadal posiadać klasę `CreateWorkflowCommand`, ale wire name powinien być jawny i stabilny.

Przykładowy manifest:

```python
COMMAND_CONTRACTS = {
    "execution.workflow.create": CommandContract(
      command_name="execution.workflow.create",
    command_class=CreateWorkflowCommand,
        target_service="execution",
        schema_version=1,
    ),
}
```

`command_name` jest stabilną tekstową nazwą kontraktu przesyłaną po wire. Nie należy mylić go z `command_type`, które powinno oznaczać klasę/typ obiektu w kodzie, a nie wartość tekstową. W tym projekcie `command_name` jest preferowane, bo jest spójne z envelope, modelem SQL i routingiem.

Alternatywnie kontrakt może być deklarowany na klasie, ale registry nadal powinno walidować duplikaty:

```python
class CreateWorkflowCommand:
    command_name = "execution.workflow.create"
    schema_version = 1
```

Preferowany jest manifest w composition root, ponieważ nie wprowadza technicznej wiedzy o transporcie do modelu commandu.

### Payload

Payload powinien zawierać wyłącznie dane potrzebne do wykonania komendy. Nie umieszczać w nim obiektów ORM, tokenów, haseł ani danych diagnostycznych.

Metadane transportowe muszą być poza payloadem:

```text
kind
command_name
schema_version
command_id
outbox_id
source_service
target_service
issued_at
correlation_id
causation_id
```

## 5. Docelowy envelope

Obecny `CommandDeliveryEnvelope` jest dobrym początkiem. Docelowy kształt:

```python
@dataclass(frozen=True, slots=True)
class CommandDeliveryEnvelope:
    kind: Literal["command"]
    command_id: str
    outbox_id: str
    command_name: str
    schema_version: int
    issued_at: datetime
    source_service: str
    target_service: str
    payload: dict[str, object]
    correlation_id: str
    causation_id: str
```

### Pola i decyzje

- `command_id` identyfikuje intencję biznesową i pozostaje stały przy redelivery.
- `outbox_id` identyfikuje konkretny rekord technicznego dostarczenia.
- `issued_at` oznacza moment utworzenia/wydania komendy.
- `published_at` oznacza potwierdzone przekazanie do brokera.
- `received_at` oznacza zapis w inboxie odbiorcy.
- `processed_at` oznacza udane wykonanie przez handler.
- `source_service` wskazuje nadawcę.
- `target_service` ogranicza routing i jest walidowany przez odbiorcę.
- `schema_version` jest częścią kontraktu i musi być przechowywany w outbox oraz inbox.
- `correlation_id` śledzi całą operację.
- `causation_id` wskazuje event/command, który wywołał tę komendę.

`command_id` i `outbox_id` nie powinny być tym samym polem. Techniczne ponowne zapisanie tej samej intencji powinno być wykrywalne, a różne intencje wykonania powinny mieć różne `command_id`.

## 6. Model SQL

### `outbox_command`

Docelowo:

```text
outbox_id              PK
command_id             NOT NULL
command_name           NOT NULL
schema_version         NOT NULL
source_service         NOT NULL
target_service          NOT NULL
issued_at              NOT NULL
payload                NOT NULL
correlation_id         NOT NULL
causation_id           NOT NULL
published_at           NULL
attempt_count          NOT NULL DEFAULT 0
next_attempt_at        NULL
last_attempted_at      NULL
last_error_code        NULL
last_error_message     NULL
created_at             NOT NULL
```

Ograniczenia:

```text
UNIQUE(source_service, command_id)
CHECK(source_service <> target_service)      # tylko jeżeli command ma być cross-BC
INDEX(target_service, published_at, issued_at)
INDEX(published_at, next_attempt_at, issued_at)
```

Jeżeli platforma ma wspierać także komendy lokalne, nie wymuszać `source_service <> target_service`; lokalne komendy nie powinny jednak trafiać do brokera przypadkiem.

### `inbox_command`

Obecne `InboxStateMixin` dostarcza dobry lifecycle. Dodać/utrzymać:

```text
id                     lokalny PK odbiorcy
outbox_id              referencja do nadawcy
command_id             identyfikator intencji
command_name           NOT NULL
schema_version         NOT NULL
source_service         NOT NULL
target_service          NOT NULL
issued_at              NOT NULL
received_at            NOT NULL
payload                NOT NULL
correlation_id         NOT NULL
causation_id           NOT NULL
status / retry / lease / error fields z InboxStateMixin
```

Ograniczenia:

```text
UNIQUE(source_service, outbox_id)
UNIQUE(source_service, command_id)
CHECK(target_service = lokalny service name)
```

`outbox_id` nie powinien być unique globalnie bez `source_service`, ponieważ różne bazy i niezależne instalacje mogą generować techniczne ID z różnych przestrzeni.

### Retencja

Po udanym przetworzeniu:

- inbox jest przechowywany przez okres wymagany audytem i retry replay;
- payload może być anonimizowany po okresie retencji, jeżeli polityka bezpieczeństwa tego wymaga;
- outbox nie może być usuwany przed potwierdzeniem publikacji i okresem diagnostycznym;
- usuwanie powinno odbywać się partiami, z metryką i ochroną przed usunięciem rekordów `PENDING`/`RETRY`.

## 7. Transakcyjny zapis commandu

### Komenda wywołana przez zmianę domeny

Jeżeli process manager lub handler zmienia własny stan i tworzy command dla innego BC, zapis musi być w tej samej transakcji:

```text
BEGIN
  zmiana stanu process managera
  INSERT outbox_command
COMMIT
```

Do tego potrzebny jest writer korzystający z aktywnej sesji/UoW:

```python
await command_outbox_writer.append(
    session=session,
    command=command,
    target_service="execution",
)
```

Writer nie wykonuje samodzielnego `commit()`.

### Komenda utworzona poza UoW

Dla komendy pochodzącej z zewnętrznego adaptera można zachować osobną sesję, ale nazwa powinna wskazywać tę odpowiedzialność:

```text
StandaloneSqlCommandOutboxWriter
```

Nie wolno używać tego wariantu tam, gdzie command i zmiana stanu mają być atomowe.

### Zmiana obecnej klasy

Rekomendacja:

```text
SqlCommandOutboxPublisher -> SqlCommandOutboxWriter
```

Wprowadzić najpierw alias/deprecation, a po przepięciu wszystkich wywołań usunąć starą nazwę. Publiczne API powinno operować na `AsyncCommandDispatcher` lub `CommandOutboxWriter`, nie na szczegółach SQL.

## 8. Relay i retry

### Docelowy lifecycle relaya

Nie trzymać locka SQL przez cały czas wywołania RabbitMQ:

```text
1. claim batch w krótkiej transakcji
2. ustaw claimed_by / lease_until
3. commit
4. publikuj rekordy poza transakcją
5. dla każdego rekordu wykonaj warunkowy mark published albo schedule retry
```

Warunek aktualizacji powinien zawierać `outbox_id` i `claimed_by`, aby późny worker nie nadpisał stanu rekordu przejętego przez inny worker.

### Retry

Retry outboxa powinien przechowywać:

```text
attempt_count
next_attempt_at
last_attempted_at
last_error_code
last_error_message
```

Wymagana polityka:

- exponential backoff z limitem;
- jitter dla wielu workerów;
- osobny limit prób transportowych;
- dead-letter outbox albo trwały status `FAILED`, gdy publikacja nie może się udać;
- alert na wiek najstarszego pending commandu;
- ręczny replay tylko z autoryzowanego narzędzia i z zachowaniem `command_id`.

Rabbit publisher confirms powinny pozostać włączone. `mandatory=True` powinno pozostać włączone, aby unroutable message był błędem, a nie pozornym sukcesem.

## 9. Routing i izolacja BC

Każdy consumer powinien wiązać wszystkie komendy skierowane do jego BC, a nie
filtrować ich po odebraniu:

```text
command.execution.workflow.create
command.execution.workflow.change
command.scheduling.scheduler_job.create
```

Rekomendowany routing key:

```text
command.<target_service>.<command_name>
```

Przykład:

```text
command.execution.execution.workflow.create
```

albo krótszy, jeżeli `command_name` już zawiera namespace:

```text
command.execution.workflow.create
```

Wybrać jeden format i objąć go testem kontraktowym.

Dodatkowe zasady:

- każdy BC ma osobną durable queue;
- queue ma binding `command.<target_service>.#` dla własnego BC;
- exchange i queue mają ACL per service;
- `target_service` w envelope pozostaje metadaną kontraktu i jest zgodny z routingiem;
- nieznany command contract trafia do DLQ, nie do nieskończonego retry;
- command nie jest broadcastem. Zwykle ma jednego właściciela wykonania.

## 10. Registry i deserializacja

### Zmienić

Obecne automatyczne wyszukiwanie plików `commands/*.py` i klucze oparte o `item.__name__` są wygodne lokalnie, ale za słabe jako publiczny kontrakt.

Docelowo:

```text
per-BC CommandContractRegistry
  -> tylko kontrakty obsługiwane przez dany BC
  -> jawna wire name
  -> command class
  -> obsługiwane schema versions
  -> target service
```

Registry powinno fail-fast podczas startu, gdy:

- wire name jest zduplikowane;
- command class nie ma handlera;
- schema version jest nieobsługiwana;
- command należy do innego target service;
- kontrakt nie ma testu wire format.

### Deserializacja

`CommandDeserializer` powinien:

1. zweryfikować `target_service` i `command_name` przed konstrukcją obiektu;
2. sprawdzić obsługiwaną wersję schematu;
3. uruchomić upcaster dla starszych wersji;
4. odrzucić nieznane pola, chyba że kontrakt jawnie dopuszcza rozszerzenia;
5. zbudować niemutowalną komendę;
6. zwrócić błąd klasyfikowany jako permanentny albo retryable.

Nie używać pickle ani dynamicznego importu na podstawie danych z brokera.

## 11. Inbox i wykonanie

Obecny `CommandInboxProcessor` powinien pozostać cienkim adapterem:

```text
claim -> validate -> deserialize -> set tracing context
      -> CommandBus -> handler -> local outbox + ack
```

Gwarancja ma być jawnie opisana jako `at-least-once`, nie `exactly-once`.

Wymagania:

- efekt handlera, lokalny event outbox i ack inboxa w jednej transakcji;
- ponowne dostarczenie tej samej komendy musi być bezpieczne;
- operacje nieidempotentne muszą korzystać z `command_id`/dedup store;
- lease nie może wygasnąć podczas długiego handlera bez heartbeat;
- błąd walidacji i nieznany kontrakt nie powinny być retryowane jak awaria DB;
- błąd DB/brokera powinien być retryable;
- DLQ musi przechowywać kod, przyczynę, payload referencyjny i correlation ID.

## 12. Bootstrap i rejestracja

Dla każdego BC, który wysyła lub odbiera komendy, zarejestrować osobno:

```text
CommandBus
CommandContractRegistry
SqlCommandOutboxWriter
RabbitCommandDeliveryTransport
CommandOutboxRelay
RabbitCommandInboxConsumer
CommandInboxProcessor
Command delivery metrics
Command worker heartbeat
```

W `main.py` uruchomić dwa niezależne workery, jeśli BC pełni obie role:

```text
event outbox relay
command outbox relay
```

Nie łączyć ich w jeden typowany relay z unionem, jeżeli pogarsza to routing, metryki lub politykę retry.

Kontenery powinny otrzymywać przez DI:

```text
session_factory
persistence_delivery_models.commands
command_contract_registry
command transport
target service name
retry policy
worker identity
```

Nie tworzyć globalnego registry wszystkich BC w mikroserwisie. Każdy proces ładuje własne komendy oraz jawnie zadeklarowane publiczne kontrakty, które może przyjmować.

## 13. Security i governance

Minimalne wymagania produkcyjne:

- TLS/mTLS między usługą a brokerem;
- osobny RabbitMQ user/vhost per środowisko;
- ACL exchange/queue per BC;
- walidacja `source_service` i `target_service`;
- autoryzacja operacji w handlerze, niezależnie od pola `source_service`;
- limit rozmiaru payloadu;
- brak sekretów i PII w logach;
- maskowanie payloadu w błędach i metrykach;
- audyt kto i kiedy wykonał replay/DLQ retry;
- rotacja credentials i certyfikatów;
- schema compatibility check w CI przed wdrożeniem.

Samo `source_service` nie jest dowodem tożsamości. To metadana diagnostyczna; tożsamość transportu musi być zapewniona przez broker i mTLS/ACL.

## 14. Observability

Metryki command outbox:

```text
command_outbox_pending_total{source_service,target_service}
command_outbox_oldest_age_seconds{source_service,target_service}
command_outbox_publish_attempts_total{command_name,result}
command_outbox_publish_failures_total{command_name,error_code}
command_outbox_publish_latency_seconds{command_name}
```

Metryki command inbox:

```text
command_inbox_pending_total{service,command_name}
command_inbox_retry_total{service,command_name,error_code}
command_inbox_dead_letter_total{service,command_name,error_code}
command_inbox_processing_latency_seconds{service,command_name}
command_inbox_duplicate_total{service,command_name}
```

Log strukturalny powinien zawierać:

```text
command_id
outbox_id
source_service
target_service
command_name
schema_version
correlation_id
causation_id
worker_id
attempt_count
```

Nie logować całego payloadu domyślnie.

## 15. Testy wymagane do enterprise readiness

### Unit

- jawna wire name każdego commandu;
- brak duplikatów w registry;
- poprawna serializacja i deserializacja;
- upcasting wersji `N-1 -> N`;
- odrzucenie nieznanego commandu i targetu;
- routing commandu do właściwego handlera;
- brak `Async`/`Sync` w nazwie biznesowej, jeżeli różni się tylko transport.

### Integration SQL

- command zapisuje się w outbox;
- rollback zmiany domeny usuwa również command outbox;
- commit zmiany domeny utrwala command outbox;
- writer nie wykonuje ukrytego commitu w aktywnym UoW;
- retry aktualizuje `attempt_count` i `next_attempt_at`;
- wygasły lease może przejąć inny worker;
- dwa workery nie publikują tego samego rekordu jednocześnie;
- publikacja po sukcesie ustawia `published_at` warunkowo;
- schema migracji odpowiada modelowi ORM.

### Integration Rabbit/system

- producer BC publikuje do właściwego routing key;
- tylko targetowy consumer zapisuje komendę do inboxa;
- consumer innego BC jej nie otrzymuje;
- ack brokera następuje dopiero po trwałym insercie inboxa;
- redelivery nie tworzy drugiego efektu biznesowego;
- awaria między efektem i ackiem jest bezpieczna;
- permanent validation error trafia do DLQ;
- transient DB/broker error powoduje requeue/retry;
- correlation i causation ID przechodzą cały łańcuch.

### Contract tests

Dla każdego publicznego commandu przechowywać fixture wire JSON i testować:

```text
producer encode == fixture
consumer decode == expected command
older schema upcasts correctly
unknown fields/version fail according to policy
```

## 16. Kolejność wdrożenia

### P0 — naprawa poprawności przepływu

1. Zdecydować, które przypadki naprawdę wymagają async command.
2. Wprowadzić `target_service` i jawne routing keys.
3. Podłączyć `RabbitCommandDeliveryTransport`, command relay i command worker w producerach.
4. Dodać test systemowy producer→broker→inbox→processor.
5. Rozdzielić kolejki commandów per target BC.

### P1 — atomowość i stabilny kontrakt

1. Zmienić `SqlCommandOutboxPublisher` na `SqlCommandOutboxWriter`.
2. Dodać wariant writer działający na aktywnej sesji/UoW bez własnego commitu.
3. Dodać `command_id`, `source_service`, `target_service`, `schema_version`.
4. Zastąpić nazwy klas namespacowanymi wire names.
5. Wprowadzić per-BC `CommandContractRegistry`.
6. Dodać migracje Alembic i testy metadata.

### P2 — niezawodność enterprise

1. Przenieść relay na claim/lease bez locka podczas wywołania brokera.
2. Dodać retry state i backoff po stronie outboxa.
3. Dodać permanent failure/DLQ dla outboxa.
4. Dodać metryki, alerty i dashboard backlogu.
5. Dodać security ACL/mTLS oraz limity payloadu.

### P3 — governance i utrzymanie

1. Dodać contract fixtures i compatibility checks w CI.
2. Dodać politykę deprecacji komend i wersji schematów.
3. Dodać kontrolowany replay z audytem.
4. Usunąć automatyczne odkrywanie kontraktów z runtime albo ograniczyć je do generatora manifestu.
5. Usunąć alias starej nazwy dopiero po migracji wszystkich konsumentów.

## 17. Kryteria zakończenia

Model można uznać za enterprise-ready, gdy:

- każda komenda ma jednego jawnego właściciela wykonania;
- command i event mają osobne typy, transporty, registry, tabele i routing;
- lokalna komenda używa `CommandBus`, bez niepotrzebnego brokera;
- async command jest zapisywany atomowo z własnym stanem process managera;
- nie ma ukrytego commitu w writerze używanym wewnątrz UoW;
- relay commandów jest podłączony produkcyjnie i monitorowany;
- routing nie używa szerokiego `command.#` jako konfiguracji produkcyjnej;
- wire name nie zależy od nazwy klasy Python;
- `command_id` jest niezależny od `outbox_id`;
- schema version i upcaster są testowane kontraktowo;
- retry, lease, DLQ, dedup i tracing są sprawdzone testem systemowym;
- migracje, metryki, security i runbook są częścią tej samej zmiany.

## Wniosek

Obecna architektura ma właściwy kierunek: command nie jest eventem, a outbox jest mechanizmem niezawodnego dostarczenia. Nie jest jednak jeszcze pełną implementacją enterprise, ponieważ command outbox nie ma domkniętej ścieżki produkcyjnej, routing jest zbyt szeroki, kontrakt opiera się na nazwie klasy, a zapis komendy nie jest transakcyjnie związany ze zmianą domeny.

Najważniejsza refaktoryzacja nie polega na dodaniu `Async` do nazw komend. Polega na jawnym rozdzieleniu:

```text
Command             = co ma zostać wykonane
CommandDispatcher   = w jaki sposób intencja jest wysłana
OutboxWriter        = jak intencja jest trwale zapisana
Relay               = jak trafia na broker
InboxProcessor      = jak jest wykonana u właściciela
```

Dopiero po wdrożeniu P0 i P1 można wiarygodnie powiedzieć, że asynchroniczne komendy są w SHELL obsługiwane jak w dojrzałym systemie mikroserwisowym.
