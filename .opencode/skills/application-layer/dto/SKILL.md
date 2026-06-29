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

## 3. DTO a Pydantic — Kiedy Używać

| Sytuacja | Rekomendacja |
|----------|-------------|
| API wejściowe (FastAPI) | Pydantic (walidacja + dokumentacja) |
| Wewnętrzne DTO aplikacji | `@dataclass(frozen=True)` (prostsze, szybsze) |
| Event payload | `@dataclass(frozen=True)` lub Pydantic |
| Między BC (integracja) | `@dataclass(frozen=True)` (niezależność od frameworka) |
| Konfiguracja | Pydantic Settings |

## 4. Lokalizacja DTO

```
# Kontrakty między BC (własność źródłowego BC)
shell/domain/<bc>/contracts/<nazwa>_dto.py

# Komendy i Query w aplikacji
shell/application/<bc>/commands/<command>.py
shell/application/<bc>/queries/<query>.py

# DTO odpowiedzi
shell/application/<bc>/dto/<entity>_dto.py
```

## 5. Podsumowanie — Checklista

Tworząc DTO:
- [ ] Własność źródłowego BC (w kontraktach)
- [ ] Lokalizacja: aplikacja (CQRS) lub kontrakty (między BC)
- [ ] Mapowany na VO przez mapper w docelowym BC
- [ ] Testy serializacji (do JSON i z JSON)
