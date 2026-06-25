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

Kluczowe:
- Port jest w **domenie lub aplikacji BC który go potrzebuje** (tu: Ordering)
- Port operuje na **własnych typach BC** (tu: `InvoiceSummary` — VO zdefiniowany przez Ordering)
- Port NIE używa typów z Invoicing BC
- Port definiuje tylko to czego BC naprawdę potrzebuje — nie całe API Invoicing

## Adaptery — implementacja portów

Adapter jest w `infrastructure/<bc>/adapters/` i implementuje port. Jest jedynym miejscem które zna oba BC.

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

## Sync vs Async — kiedy która komunikacja

Stosuj gdy:
- BC A potrzebuje danych z BC B natychmiast (w tej samej transakcji logicznej, choć nie fizycznej)
- Operacja jest szybka (odczyt, proste zapytanie)
- BC B jest dostępne (nie może być zawodne)

### Asynchroniczna (event-driven)

BC A emituje event, BC B subskrybuje i reaguje.

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

Port (`InvoicePort`) pozostaje identyczny. Handler go używający też.

## Kiedy czytasz references

- Budujesz adapter tłumaczący model zewnętrzny na wewnętrzny → `references/acl-pattern.md`
- Projektujesz nowy port między BC → `references/bc-contracts.md`

## Konwencje

- Każdy BC ma własny DI container
- Komunikacja między BC: sync przez QueryService, async przez eventy
