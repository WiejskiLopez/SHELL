---
name: validation
description: Zasady walidacji w architekturze hexagonalnej CQRS — walidacja strukturalna na granicy API (Pydantic), walidacja biznesowa w domenie, walidacja komend w aplikacji, reguły walidacji krzyżowej. Używaj gdy projektujesz walidację wejściową, definiujesz reguły dla komend, albo rozdzielasz walidację między warstwy.
---

# Validation w Enterprise DDD

## 1. Trzy Poziomy Walidacji

```
Warstwa API (Pydantic)    → strukturalna: typy, formaty, zakresy
Warstwa Aplikacji (Handler) → koordynacyjna: autoryzacja, stan systemu
Warstwa Domeny (Agregat/VO)  → biznesowa: invarianty, reguły, proces
```

## 2. Lokalizacja

```
# Walidacja strukturalna (API) — bez podkatalogu requests/, requesty leżą w api/
shell/<service>/framework/<bc>/<aggregate>/api/<nazwa>_request.py

# Walidacja komend (aplikacja) — per agregat
shell/<service>/application/<bc>/<aggregate>/commands/<command>.py  # __post_init__

# Walidacja biznesowa (domena) — per agregat
shell/<service>/domain/<bc>/aggregates/<aggregat>/value_objects/<nazwa>.py     # __post_init__
shell/<service>/domain/<bc>/aggregates/<agregat>/<agregat>.py       # guard clauses
shell/<service>/domain/<bc>/aggregates/<agregat>/exceptions/        # dedykowane wyjątki domenowe
shell/platform/domain/base/specification.py                         # Specification base (wzorzec docelowy)
```

## 3. Podsumowanie — Checklista

Projektując walidację:
- [ ] Każdy poziom ma własne błędy (API → HTTP 422, handler → domenowe)
- [ ] Testy dla każdego poziomu walidacji
