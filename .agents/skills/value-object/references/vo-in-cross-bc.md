# VO w integracji między Bounded Context

> Wyciągnięte z `bounded-context-integration/references/bc-contracts.md`.

## Zasada własności

| Element | Własność | Lokalizacja |
|---------|----------|-------------|
| VO (model wewnętrzny) | BC potrzebujący | `domain/<bc>/value_objects/` |

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

## Checklista dla VO w kontrakcie między BC

- [ ] VO jest w `domain/<bc_potrzebujacy>/value_objects/`
