---
name: domain-invariant
description: Wzorce implementacji invariantów biznesowych w DDD — reguły które muszą być zawsze spełnione, defensive checks, guard clauses, Rule Objects, walidacja między polami, invariants przy tworzeniu i modyfikacji. Używaj gdy projektujesz reguły biznesowe w agregatach/encjach/VO, albo refaktoryzujesz rozproszoną walidację.
---

# Domain Invariant / Business Rule w Enterprise DDD

## 1. Czym jest Invariant

**Invariant** to reguła biznesowa, która **zawsze musi być spełniona** — bez żadnego okna czasowego. Jeśli invariant jest naruszony, system jest w niepoprawnym stanie.

Przykłady:
- `Execution.status` nie może być `COMPLETED` i `FAILED` jednocześnie
- `OrderItem.quantity` musi być > 0
- `Payment.amount` nie może przekraczać `Order.total`
- `DateRange.end` musi być >= `DateRange.start`

## 2. Gdzie Umieszczać Invarianty

| Miejsce | Rodzaj invariantu | Przykład |
|---------|------------------|----------|
| `VO.__post_init__()` | Wewnętrzna spójność VO | `Version >= 1` |
| `Entity` / `Aggregate` metoda | Reguła stanu | `can't cancel completed execution` |
| `Aggregate` factory method | Reguła tworzenia | `graph must be active` |
| `Domain Service` | Reguła międzyagregatowa | `total items <= credit limit` |

## 3. Lokalizacja

```
# Rule Objects
shell/domain/<bc>/rules/<nazwa_reguly>_rule.py

# Wyjątki domenowe
shell/domain/<bc>/exceptions.py
shell/domain/platform/exceptions.py

# Invarianty w agregatach
shell/domain/<bc>/aggregates/<agregat>.py  # _assert_* methods
```

## 4. Podsumowanie — Checklista

Implementując invarianty:
- [ ] Brak ogólnych wyjątków (`ValueError`, `RuntimeError`) — tylko domenowe
- [ ] Testy dla każdego invariantu (pozytywne i negatywne)
