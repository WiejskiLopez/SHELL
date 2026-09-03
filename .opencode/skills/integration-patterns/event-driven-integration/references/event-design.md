# Projektowanie eventów domenowych i integracyjnych

> Uwaga: poniższe przykłady są ilustracyjne (uproszczone identyfikatory i typy). Realna klasa bazowa `DomainEvent` w SHELL ma **trzy** pola ValueObject: `event_id`, `aggregate_id`, `occurred_at`. Osobne metadane koperty (`correlation_id`, `causation_id`, `schema_version`, `integration_event_name`) dodaje platforma dopiero w outbox/inbox i kopercie transportu — nie są polami klasy domenowej.

## Struktura eventu

Event domenowy i integracyjny mają jasno rozdzielone części — payload biznesowy oraz metadane:

```python
# Metadane koperty (nadawane przez platformę, nie przez klasę eventu):
#   integration_event_name, event_id, occurred_at, schema_version,
#   correlation_id, causation_id, aggregate_id

@dataclass(frozen=True)
class OrderConfirmedIntegrationEvent:
    # ─── Payload domenowy ───
    order_id: str
    customer_id: str
    total_amount: Decimal
    items: tuple[OrderItemSnapshot, ...]
```

### Pola koperty (envelope)

| Pole | Typ | Opis |
|------|-----|------|
| `integration_event_name` | str | Stabilna nazwa publicznego kontraktu (np. `OrderConfirmed`) |
| `event_id` | str | Unikalny identyfikator tego wystąpienia eventu |
| `aggregate_id` | str | ID agregatu który wyemitował event |
| `occurred_at` | datetime | Kiedy zdarzenie zaszło (czas domenowy) |
| `correlation_id` | str \| None | ID procesu biznesowego (łączy eventy w jeden łańcuch) |
| `causation_id` | str \| None | ID eventu który bezpośrednio to spowodował |
| `schema_version` | int | Wersja schematu eventu (dla ewolucji) |

### Payload domenowy

Zawiera TYLKO dane które się wydarzyły — fakty, nie instrukcje.

```python
# POPRAWNIE — fakt biznesowy
@dataclass(frozen=True)
class PaymentCompletedEvent(DomainEvent):
    payment_id: str
    order_id: str
    amount: Decimal
    currency: str
    payment_method: str

# ŹLE — instrukcja co zrobić
@dataclass(frozen=True)
class DoProcessPaymentEvent(DomainEvent):
    order_id: str
    instruction: str  # "Charge the customer and send email"
```

## Rodzaje eventów

### Domain Event

Emitowany przez agregat, konsumowany wewnątrz tego samego bounded context. Leży w `shell/<service>/domain/<bc>/aggregates/<agregat>/events/`.

```python
# shell/<service>/domain/ordering/aggregates/order/events/order_confirmed_event.py
@dataclass(frozen=True)
class OrderConfirmedEvent(DomainEvent):
    order_id: str
    confirmed_at: datetime
```

### Integration Event

Publikowany poza bounded context. Leży w `shell/<service>/application/<bc>/<aggregate>/integration_events/`. Różnica: integration event jest kontraktem między BC — nie zmieniasz go bez zgody konsumentów.

```python
# shell/<service>/application/ordering/order/integration_events/order_completed_integration_event.py
@dataclass(frozen=True)
class OrderCompletedIntegrationEvent:
    """Publikowany do innych BC po zakończeniu zamówienia."""
    event_id: str
    occurred_at: datetime
    order_id: str
    customer_id: str
    total_amount: Decimal
```

### Kiedy Domain Event a kiedy Integration Event?

Domain Event: wewnątrz BC, niestabilny kontrakt, możesz go zmieniać.
Integration Event: między BC, stabilny kontrakt, zmiana wymaga wersjonowania.

**Aplikacyjny Event Handler obsługuje Integration Events.** Domain Event jest
wewnętrznym faktem agregatu: `append_event()` → UoW stage'uje →
`ReflectiveIntegrationMapper` mapuje na **Integration Event** → `outbox_event`.
W ramach reakcji handler może publikować kolejne Integration Events (do innych BC).

## Wersjonowanie eventów

Schemat eventu ewoluuje. Dodajesz pole, zmieniasz typ, usuwasz pole. Konsumenci którzy jeszcze nie zaktualizowali swojej logiki nie powinni się wyłożyć.

### Zasada: dodawaj, nie usuwaj

Dodanie nowego pola — inkrementuj `schema_version`, stary konsument ignoruje nowe pole.
Usunięcie pola — nigdy nie usuwaj. Zamiast tego oznacz jako deprecated + ignoruj u konsumentów. Usuń fizycznie dopiero gdy WSZYSCY konsumenci przeszli na nowy schemat.

```python
@dataclass(frozen=True)
class OrderConfirmedEventV1(DomainEvent):
    schema_version: int = 1
    order_id: str
    customer_id: str


@dataclass(frozen=True)
class OrderConfirmedEventV2(DomainEvent):
    schema_version: int = 2
    order_id: str
    customer_id: str
    confirmed_by: str | None = None  # NOWE POLE (opcjonalne dla V1 konsumentów)
```

### Backward compatibility — deserializacja

Event musi dać się zdeserializować ze starego formatu. W SHELL deserializację integration eventów obsługuje `IntegrationEventDeserializer` (z rejestrem `integration_event_name` → klasa) oraz upcaster — klasa eventu domenowego NIE posiada `from_payload()`:

```python
# Realny mechanizm:
IntegrationEventDeserializer.deserialize(
    integration_event_name, occurred_at, payload, schema_version, **envelope_metadata,
)
    -> upcast(stary payload do aktualnego modelu)
    -> IntegrationEvent / DomainEvent
```

### Zasady ewolucji

| Zmiana | Czy bezpieczna | Uwagi |
|--------|---------------|-------|
| Dodanie opcjonalnego pola | Tak | Stary konsument ignoruje |
| Dodanie wymaganego pola | Nie | Złamie starych konsumentów — nowa wersja eventu |
| Usunięcie pola | Nie | Nigdy nie usuwaj; deprecated + ignore |
| Zmiana typu pola | Nie | Nowa wersja eventu |
| Zmiana nazwy pola | Nie dodawaj nowego, deprecated stare | Nowa wersja |
| Zmiana znaczenia pola | Nie | Nowy event (inna nazwa) |

## Event-carried state transfer

Ile danych umieszczać w evencie? Są dwie szkoły:

### Cienki event (thin)

Event zawiera tylko ID — konsument sam sobie ładuje dane:

```python
@dataclass(frozen=True)
class OrderConfirmedEvent(DomainEvent):
    order_id: str   # tylko ID
```

### Gruby event (fat / event-carried state)

Event zawiera wszystkie dane potrzebne konsumentowi:

```python
@dataclass(frozen=True)
class OrderConfirmedEvent(DomainEvent):
    order_id: str
    customer_id: str
    items: tuple[OrderItemData, ...]
    total_amount: Decimal
    currency: str
```

### Kiedy który

**Cienki event** gdy:
- Konsument jest w tym samym BC i ma dostęp do repozytoriów
- Dane mogą się zmienić między emisją a konsumpcją (konsument chce najnowszą wersję)

**Gruby event** gdy:
- Konsument dziala w innym BC i korzysta z publicznego kontraktu zamiast repozytoriow zrodla
- Event jest źródłem danych do budowania read modelu (projekcji)
- Chcesz uniknąć N+1 (konsument nie musi wołać źródła po więcej danych)

W praktyce stosuj grube eventy dla integracji między BC. Konsument nie może polegać na tym, że źródło będzie dostępne.

## Konwencje dla eventów

- Event rozszerza `DomainEvent` (base class z metadanymi `event_id`, `aggregate_id`, `occurred_at`)
- `@dataclass(frozen=True)` — niemutowalny
- Nazwa w czasie przeszłym dokonanym
- Jeden event = jeden plik
- Ewolucję schematu obsługuje `IntegrationEventDeserializer` + upcaster (NIE `from_payload()` na klasie)
- Payload zawiera tylko fakty, nigdy instrukcje
- `schema_version` inkrementowane przy każdej zmianie struktury
