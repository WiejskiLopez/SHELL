---
name: data-transfer-object-structure
description: Reguły struktury DTO — frozen dataclass, typy proste, zero logiki biznesowej, własność źródłowego BC.
---

# DTO Structure

> Reguły struktury klasy DTO (Data Transfer Object) we wszystkich bounded contextach i warstwach.

## Definicja

- DTO — Transfer danych między warstwami/BC.
- Tylko dane, zero logiki biznesowej.
- VO — Modelowanie pojęcia biznesowego w domenie (odrębna rola).

## Klasa

- `@dataclass(frozen=True)` — immutable.

```python
@dataclass(frozen=True)
class WorkflowDto:
    id: str
    name: str
    status: str
    created_at: str
```

## Typy

- Typy proste (`str`, `int`, `float`, `bool`) zamiast VO domeny.
- JSON-serializable (bez `Decimal`, `datetime` — użyj `str`/`float`).

```python
# Dobrze
@dataclass(frozen=True)
class MoneyDto:
    amount: float
    currency: str

# Źle — typy domenowe w DTO
@dataclass(frozen=True)
class MoneyDto:
    amount: Decimal
    currency: Currency
```

## Zero logiki

- DTO nie zawiera metod biznesowych.
- Dozwolone: serializacja (`to_json()`, `from_json()`), walidacja strukturalna.

## Schema version

- Opcjonalnie `schema_version` dla ewolucji.

```python
@dataclass(frozen=True)
class WorkflowDto:
    schema_version: int = 1
    id: str
    name: str
```

## Ownership

- DTO jest własnością źródłowego BC.
- Konsumujący BC mapuje DTO na swoje własne VO (przez mapper).

## Lokalizacja

- Między BC: `shell/domain/<bc>/contracts/`
- Command: `shell/application/<bc>/commands/`
- Query: `shell/application/<bc>/queries/`
- Output: `shell/application/<bc>/dto/`
