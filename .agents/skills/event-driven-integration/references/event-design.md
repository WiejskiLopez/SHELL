# Projektowanie eventów domenowych i integracyjnych

## Struktura eventu

Każdy event domenowy i integracyjny ma obowiązkowe metadane:

```python
@dataclass(frozen=True)
class OrderConfirmedEvent(DomainEvent):
    # ─── Obowiązkowe metadane (z base class) ───
    event_id: str
    aggregate_id: str
    aggregate_type: str
    occurred_at: datetime
    correlation_id: str | None
    causation_id: str | None
    schema_version: int

    # ─── Payload domenowy ───
    order_id: str
    customer_id: str
    total_amount: Decimal
    items: tuple[OrderItemSnapshot, ...]
```

### Obowiązkowe pola każdego eventu

| Pole | Typ | Opis |
|------|-----|------|
| `event_id` | UUID / str | Unikalny identyfikator tego wystąpienia eventu |
| `aggregate_id` | str | ID agregatu który wyemitował event |
| `aggregate_type` | str | Typ agregatu (np. `"Order"`) |
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

Emitowany przez agregat, konsumowany wewnątrz tego samego bounded context. Leży w `domain/events/events/`.

```python
# shell/domain/ordering/events/events/order_confirmed_event.py
@dataclass(frozen=True)
class OrderConfirmedEvent(DomainEvent):
    order_id: str
    confirmed_at: datetime
```

### Integration Event

Publikowany poza bounded context. Leży w `application/events/` lub w shared kernel. Różnica: integration event jest kontraktem między BC — nie zmieniasz go bez zgody konsumentów.

```python
# shell/shared/events/ordering/order_completed_integration_event.py
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

Handler subskrybuje Domain Event → przetwarza → publikuje Integration Event (do innych BC).

## Nazewnictwo eventów

Eventy nazywaj w czasie przeszłym dokonanym — opisują co SIĘ STAŁO, nie co MA SIĘ STAĆ.

```
✅ OrderPlacedEvent        ← fakt: zamówienie zostało złożone
❌ PlaceOrderEvent         ← komenda: złóż zamówienie

✅ PaymentCompletedEvent   ← fakt: płatność została zakończona
❌ PaymentEvent            ← niejednoznaczne — rozpoczęcie? zakończenie? błąd?

✅ StockReservedEvent      ← fakt: stock został zarezerwowany
❌ ReserveStockEvent       ← komenda: zarezerwuj stock
```

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

Event musi dać się zdeserializować ze starego formatu:

```python
@classmethod
def from_payload(cls, payload: dict) -> "OrderConfirmedEvent":
    version = payload.get("schema_version", 1)
    if version == 1:
        return cls(
            event_id=payload["event_id"],
            aggregate_id=payload["aggregate_id"],
            aggregate_type=payload["aggregate_type"],
            occurred_at=payload["occurred_at"],
            correlation_id=payload.get("correlation_id"),
            causation_id=payload.get("causation_id"),
            schema_version=2,  # upgrade do najnowszej wersji
            order_id=payload["order_id"],
            customer_id=payload["customer_id"],
            confirmed_by=payload.get("confirmed_by"),  # brak w V1 → None
        )
    if version == 2:
        return cls(...)
    raise UnknownSchemaVersion(version)
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
- Konsument jest w innym BC i nie ma dostępu do repozytoriów źródła
- Event jest źródłem danych do budowania read modelu (projekcji)
- Chcesz uniknąć N+1 (konsument nie musi wołać źródła po więcej danych)

W praktyce stosuj grube eventy dla integracji między BC. Konsument nie może polegać na tym, że źródło będzie dostępne.

## Konwencje dla eventów

- Event rozszerza `DomainEvent` (base class z metadanymi)
- `@dataclass(frozen=True)` — niemutowalny
- Nazwa w czasie przeszłym dokonanym
- Jeden event = jeden plik
- `from_payload()` obsługuje stare wersje schematu
- Payload zawiera tylko fakty, nigdy instrukcje
- `schema_version` inkrementowane przy każdej zmianie struktury
