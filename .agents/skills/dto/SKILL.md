---
name: dto
description: Zasady projektowania DTO (Data Transfer Objects) w architekturze hexagonalnej — DTO vs VO, własność DTO przez źródłowy BC, mapowanie na VO domeny, immutable DTO, serializacja, wersjonowanie. Używaj gdy definiujesz kontrakt między BC, projektujesz odpowiedź API, albo mapujesz dane między warstwami.
---

# DTO Design w Enterprise DDD

## 1. DTO vs VO — Kluczowe Różnice

| Aspekt | DTO | Value Object |
|--------|-----|--------------|
| Cel | Transfer danych między warstwami/BC | Modelowanie pojęcia biznesowego w domenie |
| Lokalizacja | `application/`, `infrastructure/` | `domain/` |
| Zawiera logikę? | Nie (tylko dane) | Tak (behavior-rich) |
| Walidacja | Tylko strukturalna (typy, formaty) | Biznesowa (invarianty) |
| Niezmienniczość | Tak (frozen) | Tak (frozen) |
| Własność | Źródłowy BC | Domenowy kontekst |
| Serializacja | Tak (domyślnie) | Rzadko (przez mapper) |

```python
# VO — w domenie, z logiką biznesową
@dataclass(frozen=True, slots=True)
class Money(ValueObject):
    amount: Decimal
    currency: str

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

# DTO — w aplikacji, tylko dane
@dataclass(frozen=True)
class MoneyDTO:
    amount: float  # Uwaga: float, nie Decimal — dla JSON serializacji
    currency: str
```

## 2. DTO Jest Własnością Źródłowego BC

DTO jest definiowane przez BC, który jest **źródłem danych**. Konsumujący BC mapuje DTO na swoje własne VO.

```python
# shell/domain/billing/contracts/__init__.py — DTO własnością Billing BC
@dataclass(frozen=True)
class InvoiceDTO:
    id: str
    amount: float
    currency: str
    due_date: str  # ISO format
    status: str

# shell/domain/execution/... — Execution BC mapuje DTO na swoje VO
class ExecutionInvoiceMapper:
    def to_domain_payment(self, invoice_dto: InvoiceDTO) -> Payment:
        return Payment(
            amount=Money(Decimal(str(invoice_dto.amount)), invoice_dto.currency),
            due_date=Timestamp.from_iso(invoice_dto.due_date),
            status=PaymentStatus(invoice_dto.status),
        )
```

## 3. DTO jest Immutable

DTO są domyślnie immutable — `@dataclass(frozen=True)`. Jeśli DTO wymaga modyfikacji, tworzymy nowy obiekt.

```python
@dataclass(frozen=True)
class ExecutionDTO:
    id: str
    name: str
    status: str

    def with_status(self, status: str) -> ExecutionDTO:
        return dataclasses.replace(self, status=status)
```

## 4. DTO dla Komend i Query (CQRS)

DTO dla warstwy aplikacyjnej — input/output handlerów.

```python
@dataclass(frozen=True)
class CreateExecutionCommand:
    """DTO — komenda wejściowa. Walidacja strukturalna w warstwie API."""
    graph_id: str
    max_retries: int = 3
    timeout_seconds: int = 3600

@dataclass(frozen=True)
class ExecutionDTO:
    """DTO — odpowiedź z query handlera."""
    id: str
    graph_id: str
    status: str
    progress: float
    created_at: str
```

## 5. DTO z Wieloma Formatami Serializacji

DTO może mieć różne formaty dla różnych kanałów (API JSON, wewnętrzny event, plik).

```python
@dataclass(frozen=True)
class ExecutionDTO:
    id: str
    name: str
    status: str

    def to_json(self) -> dict:
        return {"id": self.id, "name": self.name, "status": self.status}

    def to_event_payload(self) -> dict:
        return {"execution_id": self.id, "status": self.status}
```

## 6. Wersjonowanie DTO

DTO między BC mogą wymagać wersjonowania. Każde DTO ma `schema_version`.

```python
@dataclass(frozen=True)
class InvoiceDTO:
    schema_version: int = 1
    id: str
    amount: float
    currency: str

    @classmethod
    def from_v1(cls, payload: dict) -> InvoiceDTO:
        return cls(
            schema_version=1,
            id=payload["id"],
            amount=payload["amount"],
            currency=payload.get("currency", "USD"),
        )

    @classmethod
    def from_v2(cls, payload: dict) -> InvoiceDTO:
        return cls(
            schema_version=2,
            id=payload["id"],
            amount=payload["total"]["amount"],
            currency=payload["total"]["currency"],
        )
```

## 7. DTO a Pydantic — Kiedy Używać

| Sytuacja | Rekomendacja |
|----------|-------------|
| API wejściowe (FastAPI) | Pydantic (walidacja + dokumentacja) |
| Wewnętrzne DTO aplikacji | `@dataclass(frozen=True)` (prostsze, szybsze) |
| Event payload | `@dataclass(frozen=True)` lub Pydantic |
| Między BC (integracja) | `@dataclass(frozen=True)` (niezależność od frameworka) |
| Konfiguracja | Pydantic Settings |

## 8. Lokalizacja DTO

```
# Kontrakty między BC (własność źródłowego BC)
shell/domain/<bc>/contracts/<nazwa>_dto.py

# Komendy i Query w aplikacji
shell/application/<bc>/commands/<command>.py
shell/application/<bc>/queries/<query>.py

# DTO odpowiedzi
shell/application/<bc>/dto/<entity>_dto.py
```

## 9. DTO a Zbiory (Collections)

DTO z kolekcjami — lista DTO zamiast nagiego `list[dict]`.

```python
@dataclass(frozen=True)
class ExecutionListDTO:
    items: tuple[ExecutionHeaderDTO, ...]
    total: int
    page: int
    page_size: int

@dataclass(frozen=True)
class ExecutionHeaderDTO:
    id: str
    name: str
    status: str
    created_at: str
```

## 10. Podsumowanie — Checklista

Tworząc DTO:
- [ ] `@dataclass(frozen=True)` — immutable
- [ ] Tylko dane, zero logiki biznesowej
- [ ] Typy proste (str, int, float, bool) zamiast VO domeny
- [ ] JSON-serializable (bez Decimal, datetime — użyj str/float)
- [ ] Własność źródłowego BC (w kontraktach)
- [ ] Schema version dla ewolucji (opcjonalnie)
- [ ] Lokalizacja: aplikacja (CQRS) lub kontrakty (między BC)
- [ ] Mapowany na VO przez mapper w docelowym BC
- [ ] Testy serializacji (do JSON i z JSON)
