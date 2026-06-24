---
name: bounded-context-integration
description: Wzorce integracji między Bounded Context — porty i adaptery, Anti-Corruption Layer, Open Host Service, DTO ownership, sync vs async, DI per BC. Używaj gdy BC A potrzebuje danych z BC B, projektujesz nowy port między domenami, budujesz ACL dla zewnętrznego systemu, albo planujesz ekstrakcję modułu na osobny serwis.
---

# Integracja między Bounded Context

Każdy Bounded Context (BC) ma własny wszechświat pojęć, własny ubiquitous language, własne modele. Integracja między BC nie może rozszczelnić tej autonomii.

## Złota zasada: żadnych bezpośrednich zależności między BC

BC A nie importuje nic z BC B poza kontraktami (porty/DTO). Nigdy nie sięga bezpośrednio do repozytoriów, agregatów, handlerów innego BC.

```
❌ application/ordering/handler → domain/invoicing/aggregates/Invoice
❌ application/ordering/handler → infrastructure/invoicing/repositories/InvoiceRepository
❌ domain/ordering/aggregates/Order → domain/invoicing/entities/Invoice

✅ application/ordering/handler → domain/ordering/ports/InvoicePort (Protocol)
                                         ↕
                              infrastructure/ordering/adapters/InvoiceAdapter
                                         ↕
                              application/invoicing/ports/queries/InvoiceQueryService
```

## Porty — kontrakty między BC

Port (Protocol) definiuje czego BC potrzebuje od świata zewnętrznego. Jest własnością BC który go potrzebuje.

```python
# shell/domain/ordering/ports/invoice_port.py
from __future__ import annotations
from typing import Protocol

from shell.domain.ordering.value_objects.invoice_summary import InvoiceSummary

class InvoicePort(Protocol):
    """Port potrzebny przez Ordering BC do pobrania danych faktury z Invoicing BC."""
    async def get_invoice_summary(self, order_id: str) -> InvoiceSummary | None: ...
    async def request_invoice_creation(self, order_id: str, amount: Decimal) -> None: ...
```

Kluczowe:
- Port jest w **domenie lub aplikacji BC który go potrzebuje** (tu: Ordering)
- Port operuje na **własnych typach BC** (tu: `InvoiceSummary` — VO zdefiniowany przez Ordering)
- Port NIE używa typów z Invoicing BC
- Port definiuje tylko to czego BC naprawdę potrzebuje — nie całe API Invoicing

## Adaptery — implementacja portów

Adapter jest w `infrastructure/<bc>/adapters/` i implementuje port. Jest jedynym miejscem które zna oba BC.

```python
# shell/infrastructure/ordering/adapters/invoice_adapter.py
from __future__ import annotations
from decimal import Decimal

from shell.domain.ordering.ports.invoice_port import InvoicePort
from shell.domain.ordering.value_objects.invoice_summary import InvoiceSummary
from shell.application.invoicing.ports.queries.invoice_query_service import InvoiceQueryService

class InvoiceAdapter(InvoicePort):
    def __init__(self, invoice_query_service: InvoiceQueryService) -> None:
        self._invoice_query_service = invoice_query_service

    async def get_invoice_summary(self, order_id: str) -> InvoiceSummary | None:
        # Woła query service z Invoicing BC (przez jego własny port)
        invoice_dto = await self._invoice_query_service.get_by_order_id(order_id)
        if invoice_dto is None:
            return None
        # Mapuje DTO Invoicing BC → VO Ordering BC
        return InvoiceSummary(
            invoice_id=invoice_dto.id,
            amount=invoice_dto.total_amount,
            status=invoice_dto.status,
        )
```

### Reguły adapterów

1. Adapter jest w `infrastructure/` BC który go potrzebuje
2. Adapter implementuje port (Protocol) z BC potrzebującego
3. Adapter wstrzykuje porty/query services z BC źródłowego (przez DI, nigdy bezpośrednio)
4. Adapter mapuje: typy źródłowe → typy docelowe (nigdy nie przepuszcza surowych DTO źródła)
5. Adapter nie zawiera logiki biznesowej — tylko tłumaczenie

## Anti-Corruption Layer (ACL)

Gdy BC komunikuje się z systemem legacy / zewnętrznym, ACL izoluje BC od "zepsutego" modelu danych zewnętrznego systemu.

```
Ordering BC          │  Anti-Corruption Layer    │  Legacy ERP System
                     │                           │
InvoiceSummary (VO)  │  ErpInvoiceAdapter        │  ERP XML/CSV z lat 90.
  id: str            │    parse_xml() →           │  <INVOICE>
  amount: Decimal    │    map_to_invoice_summary()│    <HEADER>
  status: Status     │                           │      <INVNUM>123</INVNUM>
                     │                           │      <AMT>100.00</AMT>
                     │                           │    </HEADER>
                     │                           │  </INVOICE>
```

### ACL — konkretna implementacja

```python
class ErpInvoiceAdapter(InvoicePort):
    """ACL dla legacy ERP — tłumaczy model ERP na model Ordering BC."""

    def __init__(self, erp_client: ErpClient) -> None:
        self._erp_client = erp_client

    async def get_invoice_summary(self, order_id: str) -> InvoiceSummary | None:
        raw_xml = await self._erp_client.get_invoice(order_id)
        if raw_xml is None:
            return None
        parsed = self._parse_erp_xml(raw_xml)
        return self._map_to_invoice_summary(parsed)

    def _parse_erp_xml(self, xml: str) -> ErpInvoiceData:
        # Cała brzydota ERP zamknięta tutaj
        ...

    def _map_to_invoice_summary(self, data: ErpInvoiceData) -> InvoiceSummary:
        return InvoiceSummary(
            invoice_id=str(data.invoice_number),
            amount=Decimal(data.amount),
            status=self._map_status(data.status_code),
        )

    def _map_status(self, erp_status: str) -> Status:
        # ERP: "P"=zapłacona, "W"=oczekująca, "X"=anulowana
        mapping = {"P": Status.paid(), "W": Status.pending(), "X": Status.cancelled()}
        return mapping.get(erp_status, Status.unknown())
```

### Kiedy stosować ACL

- Integracja z systemem legacy (stare API, XML, CSV, pliki płaskie)
- Zewnętrzne API którego kontrakt jest słaby/zmienny (brak wersjonowania, dziwne nazwy pól)
- Migracja — nowy system obok starego (strangler fig pattern)
- System którego nie kontrolujesz (third-party SaaS)

### Kiedy NIE stosować ACL

- Dwa BC w obrębie tego samego systemu (wystarczy port + adapter + QueryService)
- Zewnętrzne API ma dobry, stabilny kontrakt (wtedy wystarczy prosty adapter)

## Open Host Service / Published Language

Przeciwieństwo ACL. Gdy Twój BC jest używany przez wiele innych BC, udostępniasz stabilne, udokumentowane API.

```
Invoicing BC (Open Host)
┌─────────────────────────────────────────────┐
│ InvoiceQueryService (port publiczny)          │
│   get_by_order_id(order_id) → InvoiceDto     │
│   get_by_customer_id(customer_id) → list[..] │
│   get_overdue() → list[InvoiceDto]           │
│                                               │
│ InvoiceDto (Published Language)               │
│   id: str                                     │
│   order_id: str                               │
│   customer_id: str                            │
│   amount: Decimal                             │
│   currency: str                               │
│   issued_at: datetime                         │
│   due_at: datetime                            │
│   status: str  # "paid" | "pending" | "overdue"
└─────────────────────────────────────────────┘
```

DTO jest kontraktem. Każda zmiana musi być backward-compatible. Inne BC polegają na tym DTO.

## DTO vs Domain Object — co wraca z portu?

Zasada: **porty między BC zwracają DTO, nie obiekty domenowe.**

```python
# POPRAWNIE — port zwraca DTO (kontrakt)
class InvoiceQueryService(Protocol):
    async def get_by_order_id(self, order_id: str) -> InvoiceDto | None: ...

# ŹLE — port zwraca encję domenową (łamie enkapsulację BC)
class InvoiceRepository(Protocol):
    async def get_by_order_id(self, order_id: str) -> Invoice | None: ...
```

Wyjątek: porty wewnątrz jednego BC (np. repozytoria) operują na obiektach domenowych. Porty MIĘDZY BC operują na DTO.

## Sync vs Async — kiedy która komunikacja

### Synchronizna (request-response)

Port wywoływany bezpośrednio, adapter woła QueryService i zwraca wynik.

```python
class InvoicePort(Protocol):
    async def get_invoice_summary(self, order_id: str) -> InvoiceSummary | None: ...
```

Stosuj gdy:
- BC A potrzebuje danych z BC B natychmiast (w tej samej transakcji logicznej, choć nie fizycznej)
- Operacja jest szybka (odczyt, proste zapytanie)
- BC B jest dostępne (nie może być zawodne)

### Asynchroniczna (event-driven)

BC A emituje event, BC B subskrybuje i reaguje.

```python
# Ordering BC emituje:
OrderConfirmedEvent { order_id, customer_id, amount }

# Invoicing BC subskrybuje:
class CreateInvoiceOnOrderConfirmedHandler:
    async def handle(self, event: OrderConfirmedEvent) -> None:
        ...
```

Stosuj gdy:
- Operacja nie musi być natychmiastowa (eventual consistency jest OK)
- BC B może być czasowo niedostępne (event czeka w kolejce)
- Flow jest długotrwały (saga)
- Chcesz uniknąć couplingu czasowego (BC A nie czeka na BC B)

## DI per Bounded Context

Każdy BC ma własne komponenty DI. Żaden BC nie polega na kontenerze innego BC.

```
bootstrap/
  ordering/
    container.py        # DI tylko dla Ordering BC
    factory.py
  invoicing/
    container.py        # DI tylko dla Invoicing BC
    factory.py
  shared/
    container.py        # Współdzielone (np. database engine, clock)
```

Zasady:
- Kontener BC zawiera TYLKO komponenty tego BC
- Zależności między BC idą przez porty (wstrzykiwane jako adaptery)
- Adapter łączący BC A → BC B jest konfigurowany w bootstrap BC A
- Żadnego cyklicznego importu między kontenerami BC

```python
# bootstrap/ordering/container.py
class OrderingContainer(containers.DeclarativeContainer):
    # Port z innego BC jest wstrzykiwany jako adapter
    invoice_port = providers.Factory(
        InvoiceAdapter,
        invoice_query_service=invoicing_container.invoice_query_service,  # ← port z Invoicing BC
    )
```

## Ewolucja: od monolitu do mikroserwisów

Gdy BC staje się osobnym serwisem, adapter który był w procesie staje się HTTP/gRPC clientem:

```
TERAZ (monolit):                    POTEM (mikroserwis):

Ordering BC                         Ordering Service
  │                                   │
  ▼                                   ▼ (HTTP)
InvoiceAdapter                     InvoiceClient
  │                                   │
  ▼                                   ▼
InvoiceQueryService                Invoice Service REST API
  │
  ▼
SQLAlchemy
```

Adapter jest single point of change. Reszta Ordering BC nie zmienia się ani linijkę:

```python
# W monolocie:
class InvoiceAdapter(InvoicePort):
    def __init__(self, query_service: InvoiceQueryService) -> None: ...

# W mikroserwisie (ta sama klasa, inna implementacja):
class InvoiceHttpAdapter(InvoicePort):
    def __init__(self, http_client: httpx.AsyncClient, base_url: str) -> None: ...

    async def get_invoice_summary(self, order_id: str) -> InvoiceSummary | None:
        response = await self._http_client.get(f"{self._base_url}/invoices/{order_id}")
        if response.status_code == 404:
            return None
        return self._map_response(response.json())
```

Port (`InvoicePort`) pozostaje identyczny. Handler go używający też.

## Kiedy czytasz references

- Budujesz adapter tłumaczący model zewnętrzny na wewnętrzny → `references/acl-pattern.md`
- Projektujesz nowy port między BC → `references/bc-contracts.md`

## Konwencje

- Port (Protocol) jest własnością BC który go potrzebuje
- Adapter jest w `infrastructure/<bc>/adapters/`
- Adapter nie zawiera logiki biznesowej — tylko mapowanie
- Porty między BC zwracają DTO, nie obiekty domenowe
- Każdy BC ma własny DI container
- Komunikacja między BC: sync przez QueryService, async przez eventy
