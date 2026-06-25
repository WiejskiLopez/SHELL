# Kontrakty między Bounded Context — porty, QueryService, DTO

## Zasada własności

| Element | Własność | Lokalizacja |
|---------|----------|-------------|
| Port (Protocol) | BC potrzebujący | `domain/<bc>/ports/` |
| DTO (kontrakt danych) | BC źródłowy | `application/<bc>/dto/` |
| VO (model wewnętrzny) | BC potrzebujący | `domain/<bc>/value_objects/` |
| Adapter | BC potrzebujący | `infrastructure/<bc>/adapters/` |
| QueryService (read model) | BC źródłowy | `application/<bc>/ports/queries/` |
| SQL QueryService impl | BC źródłowy | `infrastructure/<bc>/persistence/sql/services/` |

## Przepływ danych przy komunikacji sync

```
BC A (potrzebuje danych od BC B)          BC B (źródło danych)
─────────────────────────────────         ────────────────────────

Handler w BC A:
  port.get_invoice(order_id)  ──→    InvoiceAdapter
                                         │
                                         ▼
                                     InvoiceQueryService.get_by_order_id()
                                         │
                                         ▼
                                     SQL (read model, JOIN, projekcja)
                                         │
                                         ▼
                                     InvoiceDto (BC B)
                                         │
                                     Adapter mapuje:
                                     InvoiceDto (BC B) → InvoiceSummary (BC A)
                                         │
  InvoiceSummary (BC A)  ←──────────────┘
```

## Port vs QueryService — różnica

**Port** (w BC potrzebującym): definiuje CZEGO BC potrzebuje. Język: "daj mi podsumowanie faktury dla zamówienia".

```python
# shell/domain/ordering/ports/invoice_port.py
class InvoicePort(Protocol):
    async def get_invoice_summary(self, order_id: str) -> InvoiceSummary | None: ...
    # ↑ InvoiceSummary to VO zdefiniowany przez Ordering BC
```

**QueryService** (w BC źródłowym): definiuje JAKIE DANE BC udostępnia. Język: "możesz pobrać fakturę po order_id, customer_id, statusie".

```python
# shell/application/invoicing/ports/queries/invoice_query_service.py
class InvoiceQueryService(Protocol):
    async def get_by_order_id(self, order_id: str) -> InvoiceDto | None: ...
    async def get_by_customer_id(self, customer_id: str) -> list[InvoiceDto]: ...
    async def get_overdue(self) -> list[InvoiceDto]: ...
    # ↑ InvoiceDto to DTO zdefiniowany przez Invoicing BC
```

QueryService jest:
- **Szerszy** — udostępnia wiele metod, bo wiele BC może z niego korzystać
- **Stabilniejszy** — to kontrakt publiczny BC źródłowego
- **Read-only** — nigdy nie modyfikuje stanu
- **Bezpośrednio na bazie** — może robić JOINy, projekcje, agregacje SQL bez ładowania agregatów

Port jest:
- **Węższy** — tylko to czego jeden BC naprawdę potrzebuje
- **W języku BC potrzebującego** — `InvoiceSummary`, nie `InvoiceDto`
- **Może być read i write** — może też wywoływać komendy (np. `request_invoice_creation`)

## Implementacja QueryService

```python
# shell/infrastructure/invoicing/persistence/sql/services/sql_invoice_query_service.py
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shell.application.invoicing.ports.queries.invoice_query_service import InvoiceQueryService
from shell.application.invoicing.dto.invoice_dto import InvoiceDto
from shell.infrastructure.invoicing.persistence.sql.models.invoice import InvoiceModel

class SqlInvoiceQueryService(InvoiceQueryService):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_order_id(self, order_id: str) -> InvoiceDto | None:
        result = await self._session.execute(
            select(InvoiceModel).where(InvoiceModel.order_id == order_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return InvoiceDto(
            id=model.id,
            order_id=model.order_id,
            customer_id=model.customer_id,
            amount=model.amount,
            currency=model.currency,
            issued_at=model.issued_at,
            due_at=model.due_at,
            status=model.status,
        )
```

Kluczowe: QueryService mapuje **z ORM Model bezpośrednio na DTO**, bez przechodzenia przez agregat domenowy. To jest zgodne z CQRS — odczyt pomija domenę dla wydajności.

## DTO — co to jest i gdzie leży

DTO (Data Transfer Object) to kontrakt danych między BC. Jest własnością BC źródłowego.

```python
# shell/application/invoicing/dto/invoice_dto.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass(frozen=True, slots=True)
class InvoiceDto:
    id: str
    order_id: str
    customer_id: str
    amount: Decimal
    currency: str
    issued_at: datetime
    due_at: datetime | None
    status: str
```

Reguły DTO:
- Własność BC źródłowego (`application/<bc>/dto/`)
- Proste dataclasses — zero logiki biznesowej
- Niemutowalne (`frozen=True`)
- Każda zmiana to potencjalne złamanie konsumentów — wersjonuj

## Value Object — wewnętrzny model BC potrzebującego

BC potrzebujący NIGDY nie używa DTO z innego BC bezpośrednio. Mapuje go na własny VO.

```python
# shell/domain/ordering/value_objects/invoice_summary.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True, slots=True)
class InvoiceSummary:
    invoice_id: str
    amount: Decimal
    status: str

    def __post_init__(self) -> None:
        if not self.invoice_id:
            raise ValueError("invoice_id cannot be empty")
```

Różnica między DTO a VO:
- **DTO** — kontrakt między BC, mieszka w `application/dto/`
- **VO** — wewnętrzny obiekt domenowy, mieszka w `domain/value_objects/`, ma walidację, `__post_init__`, `__str__`

## Komunikacja przez eventy — kontrakt

Gdy BC A publikuje event który konsumuje BC B, event jest kontraktem między nimi.

```python
# shell/domain/ordering/events/events/order_confirmed_event.py
@dataclass(frozen=True)
class OrderConfirmedEvent(DomainEvent):
    """Publikowany przez Ordering BC. Konsumowany przez Invoicing i Shipping BC."""
    order_id: str
    customer_id: str
    items: tuple[OrderItemData, ...]
    total_amount: Decimal
    currency: str
    confirmed_at: datetime
```

Zasady dla eventów między BC:
- Event leży w BC źródłowym (`domain/<bc>/events/events/`)
- Event jest gruby (event-carried state) — niesie wszystkie dane potrzebne konsumentom
- Konsument nie może polegać na dostępności BC źródłowego
- Zmiana eventu = zmiana kontraktu — BC źródłowe musi to koordynować z konsumentami
- Wersjonowanie eventu obowiązkowe (`schema_version`)

## Zakaz bezpośrednich zależności między BC

```
ZAKAZANE:
  shell/application/ordering/handler.py
    → from shell.domain.invoicing.aggregates.invoice import Invoice
    → from shell.infrastructure.invoicing.repositories import InvoiceRepository

DOZWOLONE:
  shell/application/ordering/handler.py
    → from shell.domain.ordering.ports.invoice_port import InvoicePort

  shell/infrastructure/ordering/adapters/invoice_adapter.py
    → from shell.application.invoicing.ports.queries.invoice_query_service import InvoiceQueryService
```

Adapter jest jedynym miejscem które importuje z innego BC. Reszta kodu BC A nigdy nie widzi symboli z BC B.

## Checklista nowego kontraktu między BC

- [ ] Port jest w `domain/<bc_potrzebujacy>/ports/`
- [ ] QueryService jest w `application/<bc_zrodlowy>/ports/queries/`
- [ ] DTO jest w `application/<bc_zrodlowy>/dto/`
- [ ] VO jest w `domain/<bc_potrzebujacy>/value_objects/`
- [ ] Adapter jest w `infrastructure/<bc_potrzebujacy>/adapters/`
- [ ] Adapter mapuje DTO źródła → VO potrzebującego (nigdy nie przepuszcza surowego DTO)
- [ ] DI rejestruje adapter w bootstrap BC potrzebującego
- [ ] BC potrzebujący nie importuje nic poza własnym portem
- [ ] Dla eventów: wersjonowanie, schema_version, backward compatibility
- [ ] Dla eventów: gruby event (event-carried state) dla integracji między BC
