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

## Porty do pobierania danych międzyagregatowych

Porty te służą do pobierania danych z innych agregatów (w obrębie tego samego BC, subdomeny lub zewnętrznego mikroserwisu) i są definiowane po stronie **konsumującego** BC.

- Port (Protocol) definiowany jest w `shell/domain/<konsumujący_bc>/services/`.
- Port zwraca tylko i wyłącznie Value Objecty domeny konsumującej — nigdy surowych DTO źródła.
- Każda metoda portu jest asynchroniczna — dane z innego agregatu/mikroserwisu są zawsze pobierane async.
- Port jest własnością potrzebującego: jeśli agregat A potrzebuje danych z agregatu B, port ląduje w `shell/domain/a/services/`, nie w `shell/domain/b/services/`.

```python
# shell/domain/execution/services/workflow_data_port.py
class WorkflowDataPort(Protocol):
    async def get_workflow_summary(self, workflow_id: WorkflowId) -> WorkflowSummary: ...
    async def get_active_workflows(self, owner_id: UserId) -> list[WorkflowSummary]: ...
```

```python
# shell/domain/execution/services/eligibility_port.py
class EligibilityPort(Protocol):
    async def check(self, customer_id: CustomerId) -> Eligibility: ...
```

### Zasady

1. **Port definiuje konsumujący** — to konsumujący wie jakie dane i w jakiej formie potrzebuje.
2. **Mapowanie na VO w adapterze** — adapter w infrastrukturze mapuje surową odpowiedź źródła na VO domeny konsumującej.
3. **Async zawsze** — pobieranie danych spoza agregatu jest zawsze asynchroniczne (nawet jeśli lokalne).
4. **Minimalizacja coupling** — jeśli agregat B zostanie wydzielony do osobnego mikroserwisu, zmienia się tylko adapter w infrastrukturze (z lokalnego repozytorium na HTTP). Port w domenie i cały kod go używający pozostaje bez zmian. Całość implementacji dla danego agregatu znajduje się w jednym folderze `infrastructure/<bc>/services/<nazwa_agregatu>/`, co umożliwia łatwe wycięcie.

```python
# Zmiana adaptera przy ekstrakcji mikroserwisu:

# Przed: adapter lokalny
class LocalWorkflowDataAdapter:
    async def get_workflow_summary(self, workflow_id: WorkflowId) -> WorkflowSummary:
        workflow = await self._repo.get_by_id(workflow_id)
        return self._mapper.to_summary(workflow)

# Po: adapter HTTP (reszta systemu bez zmian)
class HttpWorkflowDataAdapter:
    async def get_workflow_summary(self, workflow_id: WorkflowId) -> WorkflowSummary:
        raw = await self._http_client.get(f"/workflows/{workflow_id.value}/summary")
        return WorkflowSummary.from_dict(raw)
```

> **Implementacja adapterów → [port-adapter-structure](../port-adapter-structure/SKILL.md#adaptery-cross-aggregate-data-retrieval)**

## DI

- Wtryskiwany przez DI jako singleton.

## Lokalizacja

- Porty serwisów domenowych: `shell/domain/<bc>/services/`
- Porty do pobierania danych międzyagregatowych: `shell/domain/<bc>/services/`
- Adaptery: `shell/infrastructure/<bc>/services/<nazwa_agregatu>/`

## Bezpieczeństwo

- Importuje tylko z: `shell.domain.*`, biblioteka standardowa, biblioteki zewnętrzne używane w domenie (`decimal`, `dataclasses`).
- Nigdy z: `shell.infrastructure.*`, `shell.application.*`, ORM / frameworków.
