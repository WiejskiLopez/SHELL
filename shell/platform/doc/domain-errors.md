# DomainError i hierarchia wyjątków domenowych

## Cel / Co realizuje

`DomainError` (w `shell/platform/domain/exceptions/domain_error.py`) jest bazą dla błędów wywołanych naruszeniem reguł i invariantów domenowych. Na jego bazie budowane są konkretne wyjątki domenowe, m.in. `ConcurrentModificationError` (w `shell/platform/domain/exceptions/concurrent_modification_error.py`). Osobno, w warstwie aplikacji, istnieje `ApplicationError` — baza dla błędów koordynacji use case'ów.

## Problem

Błędy domenowe różnią się od błędów infrastrukturalnych: wynikają z naruszenia reguł biznesowych (guard clauses, invarianty) i powinny być rozpoznawalne przez warstwę aplikacji, by mapować je na odpowiednie odpowiedzi HTTP (np. 409 Conflict dla konfliktu współbieżności). Bez wspólnej hierarchii wyjątków aplikacja i framework nie mają jednolitego sposobu identyfikacji i obsługi błędów biznesowych.

## Realizacja techniczna

Hierarchia:

```
Exception
├── DomainError                          (warstwa domeny)
│   └── ConcurrentModificationError      (warstwa domeny)
└── ApplicationError                     (warstwa aplikacji)
```

`DomainError`:

```python
class DomainError(Exception):
    """Base class for errors caused by violated domain rules or invariants."""
```

- Podnoszony w guard clauses i metodach domenowych (patrz sekwencja guard → mutacja → event w [aggregate-root](aggregate-root.md)).
- Komunikaty budowane są po stronie konkretnych klas (np. `ConcurrentModificationError`).

`ConcurrentModificationError`:

```python
class ConcurrentModificationError(DomainError):
    """Aggregate został współbieżnie zmodyfikowany — wersja nie zgadza się przy zapisie."""

    def __init__(self, aggregate_name: str, aggregate_id: str) -> None:
        super().__init__(
            f"{aggregate_name} was concurrently modified: id={aggregate_id!r}",
        )
```

- Konstruktor przyjmuje `aggregate_name` i `aggregate_id` i buduje komunikat `"<aggregate_name> was concurrently modified: id='<aggregate_id>'"`.
- Podnoszony przy optymistycznym blokowaniu, gdy wersja agregatu przy zapisie nie zgadza się z wersją w bazie.

`ApplicationError` (`shell/platform/application/exceptions/application_error.py`):

```python
class ApplicationError(Exception):
    """Base class for errors raised while coordinating an application use case."""
```

- Baza dla błędów koordynacji use case'ów w warstwie aplikacji.
- Leży poza warstwą domeny (nie dziedziczy z `DomainError`), bo dotyczy orkiestracji, nie reguł domenowych.

Warstwy obsługi: wyjątki domenowe są rzucane w metodach domenowych, propagowane przez command handlers (które nie przechwytują ich — patrz [cqrs-buses](cqrs-buses.md)) i mapowane na odpowiedzi HTTP w warstwie framework/middleware (patrz [error-handling](error-handling.md), [http-api](http-api.md)).

## Kluczowe pliki

- `shell/platform/domain/exceptions/domain_error.py`
- `shell/platform/domain/exceptions/concurrent_modification_error.py`
- `shell/platform/application/exceptions/application_error.py`

## Powiązane koncepcje

- [aggregate-root](aggregate-root.md)
- [error-handling](error-handling.md)
- [http-api](http-api.md)
- [unit-of-work](unit-of-work.md)
