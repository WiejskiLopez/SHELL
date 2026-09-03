---
name: guard-vs-specification-decision
description: Reguły wyboru między Guard Clause a Specification w metodach domenowych — decision framework, tabela decyzyjna, przykłady miksiu.
---

# Guard Clause vs Specification — decision framework

## Zasada naczelna

Guard clause i Specification rozwiązują ten sam problem (egzekwowanie reguł biznesowych) ale na różnych poziomach abstrakcji i reuse'u. **Guard chroni invariant lokalnie i jest fail-fast. Specification enkapsuluje regułę do kompozycji i wielokrotnego użytku.**

> **Status wzorca:** baza `Specification` oraz wzorzec specyfikacji są w SHELL stanem docelowym (test arch `test_specifications_extend_specification` wymaga bazy `shell/platform/domain/base/specification.py`, która nie istnieje jeszcze w platformie — patrz `pattern-standards/specification-structure`). Do czasu wdrożenia bazy stosuj wyłącznie guard clauses.

## Kiedy Guard Clause

| Sytuacja | Przykład |
|---|---|
| Warunek **trywialny, jednorazowy** — występuje w jednej metodzie | `self._status is not OrderStatus.APPROVED` |
| Warunek dotyczy **parametru metody**, nie stanu agregatu | `if reason is None` / `if amount <= 0` |
| Null check, zakres liczby, typ | `if customer_id is None` |
| Oczywisty invariant techniczny bez logiki biznesowej | `if now < self._created_at` |

Guard rzuca dedykowany `DomainError` (subklasę) i jest pierwszą linią w metodzie.

```python
def cancel(self, reason: CancellationReason) -> None:
    if self._status is not OrderStatus.APPROVED:
        raise OrderNotApprovedError(self._id)
    ...
```

## Kiedy Specification

| Sytuacja | Przykład |
|---|---|
| **Ta sama reguła w ≥2 miejscach** | `IsVipCustomer()` używane w agregacie i repozytorium |
| Potrzebujesz **kompozycji reguł** (AND/OR/NOT) | `CanBeCancelled AND HasNoOutstandingClaims` |
| Reguła służy też do **filtrowania w DB** | Przekazana do repozytorium jako WHERE |
| Chcesz **nazwać regułę biznesową** explicit | `class HasMinimumOrderValue(Specification[Order])` |

```python
class CanBeCancelled(Specification[Order]):
    def is_satisfied_by(self, order: Order) -> bool:
        return order.status is OrderStatus.APPROVED and not order.has_open_claims
```

## Kiedy Guard używa Specification — miks

Gdy warunek jest złożony, ale sprawdzany tylko lokalnie — Specification wewnątrz guarda:

```python
def cancel(self, reason: CancellationReason) -> None:
    if not CanBeCancelled().is_satisfied_by(self):
        raise OrderCannotBeCancelledError(self._id)
    ...
```

To nie jest overengineering — Specification nazywa regułę i pozwala ją przetestować w isolation. Guard zostaje jako fail-fast wrapper.

## Tabela decyzyjna

| Cecha | Guard Clause | Specification |
|---|---|---|
| Reuse | Nie (lokalny) | Tak (wielokontekstowy) |
| Kompozycja | AND przez chain guardów | AND/OR/NOT przez pattern |
| Filtrowanie SQL | Nie | Tak |
| Testowanie | Testowane przez test metody | Osobny test jednostkowy |
| Złożoność warunku | Prosta (1-2 linie) | Dowolna |
| Zależność od stanu | Stan + parametry | Dowolne obiekty |

## Zasady

- Nie wyciągaj do Specification warunku jednorazowego i prostego — to overengineering
- Nie zostawiaj w guardzie logiki powtórzonej w 3 miejscach — refaktor do Specification
- Guard i Specification to nie konkurencja — Specification może być użyty wewnątrz guarda
- Do czasu istnienia bazy `Specification` w platformie, powtórzoną regułę wyrażaj przez `_assert_*` metody agregatu i dedykowane wyjątki (patrz `pattern-standards/domain-invariant-structure`)