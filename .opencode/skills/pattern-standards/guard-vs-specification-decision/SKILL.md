---
name: guard-vs-specification-decision
description: Reguły wyboru między Guard Clause a Specification w metodach domenowych — decision framework, tabela decyzyjna, przykłady miksiu.
---

# Guard Clause vs Specification — decision framework

## Zasada naczelna

Guard clause i Specification rozwiązują ten sam problem (egzekwowanie reguł biznesowych) ale na różnych poziomach abstrakcji i reuse'u. **Guard chroni invariant lokalnie i jest fail-fast. Specification enkapsuluje regułę do kompozycji i wielokrotnego użytku.**

## Kiedy Guard Clause

| Sytuacja | Przykład |
|---|---|
| Warunek **trywialny, jednorazowy** — występuje w jednej metodzie | `self._status is not Status.ZATWIERDZONE` |
| Warunek dotyczy **parametru metody**, nie stanu agregatu | `if powod is None` / `if kwota <= 0` |
| Null check, zakres liczby, typ | `if klient_id is None` |
| Oczywisty invariant techniczny bez logiki biznesowej | `if now < self._data_utworzenia` |

Guard rzuca `DomainError` i jest pierwszą linią w metodzie.

```python
def anuluj(self, powod: PowodAnulowania) -> None:
    if self._status is not Status.ZATWIERDZONE:
        raise DomainError("Tylko zamówienie zatwierdzone można anulować")
    ...
```

## Kiedy Specification

| Sytuacja | Przykład |
|---|---|
| **Ta sama reguła w ≥2 miejscach** | `KlientVIP()` używane w agregacie i repozytorium |
| Potrzebujesz **kompozycji reguł** (AND/OR/NOT) | `MozeBycAnulowane AND NieMaZaleglosci` |
| Reguła służy też do **filtrowania w DB** | Przekazana do repozytorium jako WHERE |
| Chcesz **nazwać regułę biznesową** explicit | `class KlientZMinimumZamowieniowym` |

```python
class MozeBycAnulowane(Specification[Zamowienie]):
    def is_satisfied_by(self, zamowienie: Zamowienie) -> bool:
        return zamowienie.status is Status.ZATWIERDZONE \
           and not zamowienie.czy_ma_otwarte_reklamacje
```

## Kiedy Guard używa Specification — miks

Gdy warunek jest złożony, ale sprawdzany tylko lokalnie — Specification wewnątrz guarda:

```python
def anuluj(self, powod: PowodAnulowania) -> None:
    if not MozeBycAnulowane().is_satisfied_by(self):
        raise DomainError("Zamówienie nie może być anulowane")
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
