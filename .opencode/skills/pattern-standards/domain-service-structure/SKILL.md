---
name: domain-service-structure
description: Reguły struktury Domain Service — stateless, operacje wieloagregatowe, porty dla zależności zewnętrznych.
---

# Domain Service Structure

> Reguły struktury klasy Domain Service we wszystkich bounded contextach.

## Definicja

- Domain Service to statelessowa operacja domenowa, która nie pasuje naturalnie do żadnej Entity ani Value Object.
- Używaj gdy: logika operuje na wielu agregatach tego samego BC, wymaga algorytmu/kalkulacji, potrzebuje koordynacji między encjami w jednej transakcji, albo nie ma stanu/tożsamości.

## Klasa

- Stateless — serwis nie przechowuje danych między wywołaniami. Wszystkie dane pochodzą z parametrów wywołania.
- Brak pól instancji poza wstrzykniętymi zależnościami (porty, inne serwisy domenowe).

```python
class PricingService:
    def __init__(self, tax_port: TaxPort, currency_converter: CurrencyConverterService) -> None:
        self._tax_port = tax_port
        self._currency_converter = currency_converter
```

## Sygnatury

- Używają VO, nie typów prostych.

```python
def calculate_order_total(self, items: list[OrderItem], customer_id: CustomerId, currency: Currency) -> Money:
    ...
```

## Zawartość

- Domain Service zawiera logikę domenową.
- Handler aplikacyjny zawiera koordynację infrastrukturalną (transakcje, eventy, repozytoria).
- Jeśli logika wymaga danych zewnętrznych — serwis definiuje Port (Protocol), implementowany przez adapter w infrastrukturze.

```python
class TaxPort(Protocol):
    async def get_tax_rate(self, customer_id: CustomerId, product_id: ProductId) -> Decimal:
        ...
```

## Kompozycja

- Domain Service może używać innych Domain Service'ów.

```python
class PricingService:
    def __init__(self, tax_service: TaxService, discount_service: DiscountService) -> None:
        ...
```

## DI

- Wtryskiwany przez DI jako singleton.

## Lokalizacja

- Domain Services: `shell/domain/<bc>/aggregates/<agregat>/services/`

Lokalizację portów komunikacji międzyagregatowej (katalog `ports/`) i ich adapterów
opisują dedykowane wzorce: Aggregate Provider i Command Port.

## Bezpieczeństwo

- Importuje tylko z: `shell.domain.*`, biblioteka standardowa, biblioteki zewnętrzne używane w domenie (`decimal`, `dataclasses`).
- Nigdy z: `shell.infrastructure.*`, `shell.application.*`, ORM / frameworków.
