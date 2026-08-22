# Transmisja eventu od agregatu do event handlera

## Zakres analizy

Opis dotyczy aktualnej implementacji eventu `AuthSessionCreatedEvent` w
bounded context `User` oraz jego konsumpcji przez `Session` BC.

Rozroznienie kontraktow:

- `DomainEvent` - wewnetrzny fakt domenowy emitowany przez agregat;
- `IntegrationEvent` - publiczna reprezentacja tego faktu dla innego BC;
- rekord `outbox_event` / `inbox_event` - techniczny zapis dostarczenia;
- `EventBus` - lokalny dispatcher wywolujacy zarejestrowane handlery.

## Trasa przez klasy

```mermaid
flowchart LR
    A[AuthSession aggregate\nAuthSession._new] --> B[AuthSessionCreatedEvent\nDomainEvent]
    B --> C[AggregateRoot.append_event\nbuffer _events]
    C --> D[SqlAlchemyUnitOfWorkBase.save\npull_events + stage_events]
    D --> E[ReflectiveIntegrationMapper.map]
    E --> F[AuthSessionCreatedIntegrationEvent\nIntegrationEvent]
    F --> G[IntegrationEventSerializer.to_envelope]
    G --> H[SQL outbox envelope\npayload + metadata]
    H --> I[(User DB\noutbox_event)]
    I --> J[OutboxToTransportRelay.run_once]
    J --> K[RabbitDeliveryTransport.deliver]
    K --> L[(RabbitMQ\nshell.delivery)]
    L --> M[RabbitInboxConsumer._persist]
    M --> N[(Session DB\ninbox_event)]
    N --> O[EventInboxProcessor.run_once]
    O --> P[EventDeserializer.deserialize]
    P --> Q[Session event registry]
    Q --> R[EventBus.publish]
    R --> S[AuthSessionCreatedEventHandler.handle]
    S --> T[Session.open\nSession aggregate]
    T --> U[SessionOpenedEvent]
    U --> V[Session BC UoW\nnowy outbox_event]
```

Pelna trasa jest asynchroniczna od momentu zapisu do `outbox_event`. Agregat
nie wywoluje bezposrednio `AuthSessionCreatedEventHandler`.

## Krok po kroku

### 1. Agregat emituje DomainEvent

Punktem poczatkowym jest metoda
[AuthSession._new](shell/user_service/domain/user/aggregates/auth_session/auth_session.py).
Po utworzeniu agregatu wywoluje ona:

```text
AuthSession.append_event(AuthSessionCreatedEvent.now(...))
```

`AuthSessionCreatedEvent` dziedziczy po
[DomainEvent](shell/platform/domain/events/domain_event.py). Jest to fakt
wewnetrzny dla User BC, zawierajacy m.in. `auth_session_id` i `user_id`.

### 2. AggregateRoot buforuje event

[AggregateRoot](shell/platform/domain/base/aggregate_root.py) w
`append_event()`:

1. uzupelnia `aggregate_id` oraz `aggregate_name`;
2. dodaje event do prywatnego bufora `_events`.

Event pozostaje w agregacie do czasu zapisania agregatu przez UoW.
`pull_events()` kopiuje bufor i go czysci.

### 3. Application handler zapisuje agregat przez UoW

Handler przypadku uzycia otwiera kontekst UoW i wywoluje `save()`.
Implementacja bazowa to
[SqlAlchemyUnitOfWorkBase](shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py):

```text
save(repo_type, aggregate)
  -> repository.save(aggregate)
  -> aggregate.pull_events()
  -> stage_events(domain_events)
```

`stage_events()` przyjmuje tylko instancje `DomainEvent`. Na tym etapie nie ma
jeszcze `IntegrationEvent`.

### 4. Commit mapuje DomainEvent na IntegrationEvent

Przy wyjsciu z `async with unit_of_work` wywolywana jest metoda `commit()`.
W jej wnetrzu najpierw wykonywane jest `_write_staged_outbox()`, czyli dodanie
rekordow outbox do tej samej sesji i transakcji SQL, a dopiero potem:

- `session.commit()` w zwyklym trybie UoW;
- `session.flush()` w trybie odroczonym, gdy transakcje kontroluje
  `InboxProcessorBase`.

Nie ma tutaj osobnego commitu pomiedzy mapowaniem eventu a zapisem outbox.

Dla `AuthSessionCreatedEvent`:

```text
ReflectiveIntegrationMapper.map(domain_event)
  -> AuthSessionCreatedIntegrationEvent
```

[ReflectiveIntegrationMapper](shell/platform/infrastructure/mapping/reflective_integration_mapper.py)
znajduje klase integracyjna na podstawie nazwy eventu i mapuje Value Objecty na
wartosci transportowe. Dla `AuthSessionCreatedEvent` wykonuje w uproszczeniu:

```text
AuthSessionCreatedEvent
  -> nazwa AuthSessionCreatedIntegrationEvent
  -> modul shell.user_service.application.user.auth_session.integration_events
  -> klasa AuthSessionCreatedIntegrationEvent
```

Jesli mapper nie znajdzie klasy, nie zwraca pustego wyniku. Rzuca
`IntegrationMappingError` w trzech przypadkach:

- modul eventu ma nieobslugiwana topologie pakietow;
- nie istnieje oczekiwany modul `integration_events`;
- modul istnieje, ale nie zawiera oczekiwanej klasy IntegrationEvent.

Po znalezieniu klasy mapper moze dodatkowo propagowac blad danych, np.
`AttributeError`, gdy DomainEvent nie ma wymaganego pola envelope, albo
`TypeError`, gdy konstruktor IntegrationEvent nie pasuje do zbudowanych pol.

Zachowuje metadane koperty:

- `event_id`;
- `occurred_at`;
- `aggregate_id` i `aggregate_name`;
- `schema_version`;
- `correlation_id` i `causation_id`.

Kontrakt eventu znajduje sie w
[auth_session_created_integration_event.py](shell/user_service/application/user/auth_session/integration_events/auth_session_created_integration_event.py).

### 5. UoW zapisuje outbox atomowo ze zmiana domenowa

[SqlAlchemyUnitOfWorkBase._write_staged_outbox](shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py)
wykonuje:

```text
IntegrationEventSerializer.to_envelope(integration_event, outbox_id)
  -> payload biznesowy
  -> metadata envelope
  -> self._models.events.outbox(...)
  -> session.add(outbox)
  -> session.add(audit)
```

`IntegrationEventSerializer.to_payload()` zwraca wylacznie dane biznesowe.
`IntegrationEventSerializer.to_envelope()` dodaje osobno:

```text
outbox_id        # identyfikator rekordu outbox nadawcy
event_id         # tozsamosc faktu
event_type
occurred_at
schema_version
correlation_id
causation_id
aggregate_id
aggregate_name
payload
```

`event_type` jest kluczem kontraktu w envelope. RabbitMQ uzywa go do zbudowania
routing key `event.<event_type>`, a odbiorca uzywa go do wyboru klasy w registry.
Nie jest polem payloadu biznesowego.

Identyfikatory transmisji maja rozne znaczenia:

```text
outbox_event.id  -> envelope.outbox_id -> inbox_event.outbox_id
inbox_event.id   -> lokalny klucz rekordu odbiorcy
event_id         -> tozsamosc faktu biznesowego
source_service   -> bounded context nadawcy
```

`outbox_id` jest referencja do rekordu nadawcy, a odbiorca generuje wlasne
`inbox_event.id` przez techniczny `TechnicalIdGenerator`. Nie ma dodatkowego
identyfikatora dostarczenia.

Nastepnie `session.commit()` zatwierdza w jednej transakcji:

```text
zmiana agregatu AuthSession + outbox_event + audit
```

W zwyklym UoW kolejnosc operacji jest wiec taka:

```text
_write_staged_outbox()
  -> session.add(outbox)
  -> session.add(audit)
  -> session.commit()
```

W trybie odroczonym `session.flush()` tylko materializuje rekordy w biezacej
transakcji. Ostateczny `COMMIT` wykonuje wtedy `InboxProcessorBase` razem z
potwierdzeniem rekordu inbox.

Dzieki temu event nie zostanie utracony po zatwierdzeniu zmiany domenowej, a
przed wyslaniem do brokera nie trzeba utrzymywac otwartej transakcji domenowej.

### 6. Relay producenta pobiera outbox

W uruchomieniu User BC kontener tworzy
[OutboxToTransportRelay](shell/platform/infrastructure/messaging/transport/outbox_to_transport_relay.py)
z `kind="event"`.

`run_once()`:

1. pobiera rekordy z `outbox_event`, dla ktorych `published_at IS NULL`;
2. buduje `DeliveryEnvelope`;
3. wywoluje `RabbitDeliveryTransport.deliver(...)`;
4. ustawia `published_at` dopiero po pozytywnym dostarczeniu;
5. zatwierdza zmiane.

Awaria pomiedzy dostarczeniem a oznaczeniem rekordu moze spowodowac ponowna
dostawe. Jest to semantyka at-least-once.

### 7. Broker przekazuje kopie do docelowego BC

RabbitMQ dostarcza kopie eventu do kolejki Session BC.

[RabbitInboxConsumer](shell/platform/infrastructure/messaging/transport/rabbit/rabbit_inbox_consumer.py):

1. dekoduje `DeliveryEnvelope`;
2. zapisuje event do lokalnego `Session DB.inbox_event`;
3. stosuje idempotentny insert;
4. wysyla ACK do RabbitMQ dopiero po zatwierdzeniu zapisu w inboxie.

Jesli proces zatrzyma sie po zapisie do inboxa, ale przed ACK, broker moze
powtorzyc dostarczenie. Idempotentny insert czyni takie powtorzenie nieszkodliwym.

### 8. EventInboxProcessor przejmuje rekord

Worker Session BC uruchamia
[EventInboxProcessor](shell/platform/infrastructure/messaging/event/processor/event_inbox_processor.py).
Klasa dziedziczy po
[InboxProcessorBase](shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py),
ktory realizuje wspolny lifecycle:

```text
claim PENDING -> PROCESSING
  -> walidacja envelope
  -> deserializacja
  -> dispatch handlera
  -> ack PROCESSED albo retry/DLQ
```

Przetwarzanie jest wykonywane w transakcji kontrolowanej przez processor. Przy
sukcesie zmiana domenowa handlera, jego outbox oraz potwierdzenie inboxa sa
zatwierdzane razem.

### 9. Deserializacja eventu

[EventInboxProcessor](shell/platform/infrastructure/messaging/event/processor/event_inbox_processor.py)
wywoluje `EventDeserializer.deserialize(...)`.

[EventDeserializer](shell/platform/infrastructure/serialization/event/event_deserializer.py)
jest fasada dla `EnvelopeDeserializer`, ktory:

1. pobiera klase po `event_type` z registry;
2. uruchamia upcaster, jezeli jest skonfigurowany;
3. odtwarza obiekt `AuthSessionCreatedIntegrationEvent` z envelope i payloadu;
4. zwraca `None` dla nieznanego lub blednego eventu.

Registry Session BC jest budowany przez
[build_session_event_registry](shell/session_service/bootstrap/session/event_registry.py).
Zawiera eventy wlasne Session BC oraz jawnie dopuszczony event User BC.

### 10. EventBus dispatchuje event do handlera

Po deserializacji processor wywoluje `EventBus.publish([event])`.

[EventBus](shell/platform/application/bus/event_bus.py):

1. wyszukuje subskrybentow po dokladnym typie eventu;
2. pobiera instancje handlerow z fabryk DI;
3. wywoluje `await handler.handle(event)`.

Subskrypcja znajduje sie w
[configure_session_container](shell/session_service/bootstrap/session/container/session_core_container.py):

```text
AuthSessionCreatedIntegrationEvent
  -> AuthSessionCreatedEventHandler factory
```

### 11. Handler wykonuje reakcje w docelowym BC

[AuthSessionCreatedEventHandler](shell/session_service/application/session/session/event_handlers/auth_session_created_event_handler.py)
reaguje na fakt z User BC:

1. otwiera UoW Session BC;
2. sprawdza, czy uzytkownik ma juz otwarta sesje;
3. jesli tak, konczy prace bez efektu biznesowego;
4. jesli nie, wywoluje `Session.open(...)`;
5. zapisuje agregat przez `unit_of_work.save(...)`.

`Session.open()` emituje kolejny event domenowy `SessionOpenedEvent`. Ten event
jest mapowany i zapisywany do outbox Session BC w tej samej transakcji co nowa
sesja. Moze wiec rozpoczac nastepny, analogiczny obieg.

## Gdzie jest granica transakcji?

```text
User BC:
  zmiana AuthSession + outbox_event -> COMMIT

Transport:
  outbox_event -> RabbitMQ -> inbox_event

Session BC:
  claim inbox
  zmiana Session + nowy outbox_event + ACK inbox -> COMMIT
```

`InboxProcessorBase._process_in_transaction()` ustawia ambientny
`DeliverySessionScope`. UoW handlera wykrywa ten scope, wykorzystuje te sama
sesje SQL i odracza wlasny commit. Ostateczny commit nalezy do processora.

## Test kanonicznego toru

Test kontraktowy
[test_integration_event_transport_contract.py](shell/tests/contracts/test_integration_event_transport_contract.py)
sprawdza caly tor bez alternatywnej sciezki:

```text
IntegrationEventSerializer
  -> outbox_event
  -> OutboxToTransportRelay
  -> EnvelopeCodec
  -> inbox_event
  -> EventInboxProcessor
  -> EventDeserializer
  -> EventBus
```

Test sprawdza zachowanie wszystkich metadanych envelope, separacje payloadu
biznesowego oraz odtworzenie IntegrationEvent po stronie konsumenta.

## Skrocona mapa odpowiedzialnosci

| Etap | Klasa | Odpowiedzialnosc |
|---|---|---|
| Emisja | `AuthSession`, `AggregateRoot` | zmiana stanu i buforowanie `DomainEvent` |
| Staging | `SqlAlchemyUnitOfWorkBase` | pobranie eventow z agregatu |
| Mapowanie | `ReflectiveIntegrationMapper` | `DomainEvent -> IntegrationEvent` |
| Serializacja | `IntegrationEventSerializer` | payload biznesowy i kompletna koperta |
| Outbox | modele `events.outbox` | trwaly zapis metadanych i payloadu |
| Relay | `OutboxToTransportRelay` | outbox do brokera |
| Transport | `RabbitDeliveryTransport`, `EnvelopeCodec` | JSON envelope i routing po `event_type` |
| Inbox | `RabbitInboxConsumer` | trwaly zapis po stronie odbiorcy |
| Processing | `EventInboxProcessor`, `InboxProcessorBase` | claim, retry, ack, transakcja |
| Deserializacja | `EventDeserializer` | payload do obiektu eventu |
| Dispatch | `EventBus` | wybor i wywolanie handlerow |
| Reakcja | `AuthSessionCreatedEventHandler` | efekt biznesowy w Session BC |

## Najwazniejszy wniosek

Rzeczywista trasa nie jest polaczeniem:

```text
Aggregate -> EventHandler
```

Tylko:

```text
Aggregate
  -> DomainEvent
  -> UnitOfWork
  -> IntegrationEvent
  -> IntegrationEventSerializer.to_envelope()
  -> outbox_event {event_type, event_id, schema_version, payload}
  -> relay / broker
  -> inbox_event
  -> InboxProcessor
  -> Deserializer
  -> EventBus
  -> EventHandler
```

Handler jest ostatnim elementem dostarczania i pierwszym elementem reakcji
biznesowej po stronie konsumenta.
