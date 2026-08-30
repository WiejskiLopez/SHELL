---
name: review-domain-layer
description: Weryfikacja warstwy domenowej — agregaty, encje, value objects, invariants, guard clauses, domain events, domain services, factory, specification, maszyny stanów. Używaj przy code review modelu domenowego.
---

# Review — Warstwa domenowa

> Domena to serce systemu. Naruszenia invariantów i ekspozycja stanu to najdroższe błędy.

## 1. Struktura agregatu / encji / VO

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Enkapsulacja stanu — brak publicznych setterów, stan tylko przez metody domenowe | `aggregate.field = value` z zewnątrz; publiczny setter "dla mappera" | **CRITICAL** |
| Referencje przez ID, nie przez obiekty | agregat trzyma encję innego agregatu zamiast jej ID | HIGH |
| `__slots__` używane, dziecko `Entity`/`AggregateRoot` dziedziczy poprawnie | brak `__slots__`; pole spoza `__slots__` | MEDIUM |
| Kolejność pól w `__slots__`: id, created_at/occurred_at, updated_at, deleted_at, biznesowe | pole biznesowe przed technicznym | LOW |
| VO to frozen dataclass dziedziczący `ValueObject`, walidacja w `__post_init__` | modyfikowalny VO; brak walidacji przy utworzeniu | **CRITICAL** |
| Brak `@dataclass` na encji/agregacie | entity jako `@dataclass` | **CRITICAL** (patrz arch-test-pytest) |
| Dzieci encji tylko wewnątrz agregatu | child entity utworzone poza agregatem | HIGH |

Patrz `aggregate-structure`, `entity-structure`, `value-object-structure`, `slot-ordering`.

## 2. Invarianty i guard clauses

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Invarianty wymuszane przy tworzeniu i przy każdej modyfikacji (`_assert_invariants`) | invariant możliwy do złamania przez legalną sekwencję metod | **CRITICAL** |
| Metody modyfikujące zaczynają się od guard clauses (fail-fast) | walidacja po mutacji | HIGH |
| Każdy warunek rzuca dedykowany wyjątek domenowy | ogólny `ValueError`/`RuntimeError` dla reguły biznesowej | HIGH |
| Brak pustych fallbacków — wartości opcjonalne jako `None`, wymagane walidowane błędem | `name or ""`, `VO(x) if x else VO("")` | **CRITICAL** (patrz no-empty-fallbacks) |
| Reguły złożone/wielokrotne w Rule Object ps. | guard z 5 warunków inline w 3 metodach | MEDIUM |

Patrz `domain-invariant`, `domain-invariant-structure`, `guard-clause-pattern`,
`guard-vs-specification-decision`, `no-empty-fallbacks`.

## 3. Domain events

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Zdarzenia emitowane w metodach domenowych, sekwencja guard → mutacja → event | event emitowany z handlera przy braku zmiany stanu | HIGH |
| Event to frozen dataclass rozszerzający `DomainEvent`, nazwa w czasie przeszłym | event jako zwykła klasa; `UserCreated` → `CreateUser` | MEDIUM |
| Event niesie dane stanu, nie cały agregat | event niesie agregat z metodami | HIGH |
| Backward compatibility sygnatury zdarzeń | change bez wersjonowania przy konsumentach | HIGH |

Patrz `domain-event-structure`, `event-semantics` (architectural-discipline).

## 4. Domain service i maszyny stanów

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Logika wieloagregatowa w domain service (stateless), nie w encji ani handlerze | kalkulacja cross-aggregate w handlerze | **CRITICAL** |
| Transakcje nie leżą w domenie | domain service zarządza UoW/commit | **CRITICAL** |
| Zależności zewnętrzne domeny za portem, zależność wstrzykiwana | domain service robi `requests.get(...)` | **CRITICAL** |
| Stan rozliczany przez enum (StrEnum) jako Value Object | status jako string/nagie `str` | HIGH |
| Tylko legalne przejścia stanów | przejście `CREATED -> CANCELLED` bez reguły | HIGH |

Patrz `domain-service`, `domain-service-structure`, `constant-and-enum-naming-standards`.

## 5. Factory i rekonstrukcja

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Factory method na VO/Entity gdy tworzenie złożone; `restore()` dla rekonstrukcji z persystencji | rekonstrukcja przez publiczne pola / `object.__new__` w kodzie produkcyjnym | HIGH |
| `restore()` nie uruchamia logiki tworzenia, która rzuci błąd na stanie zapisanym | restore wykonuje walidację "utworzeniową" | HIGH |
| Factory nie zasypuje bridge'ów zależności infrastrukturalnych | factory przyjmuje repo/infra | **CRITICAL** |

Patrz `factory`, `factory-structure`.

## 6. Specyfikacje

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Specyfikacja dziedziczy `Specification[T]`, `is_satisfied_by` | spec z innym kontraktem | MEDIUM |
| Kompozycja AND/OR/NOT zamiast duplikacji warunków w repo | warunek powtórzony w 3 repozytoriach | MEDIUM |

Patrz `specification`, `specification-structure`.

## 7. Checklista finalna

- [ ] Stan niedostępny z zewnątrz do zapisu; brak publicznych setterów.
- [ ] Wszystkie invarianty wymuszone w domenie, nie w handlerze/API.
- [ ] Eventy tylko ze zmianą stanu; sygnatury wersjonowane.
- [ ] Zero importów infrastruktury/ORM w plikach domeny.
- [ ] Rekonstrukcja tylko przez `restore()`/factory.