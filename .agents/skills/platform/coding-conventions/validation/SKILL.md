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
# Walidacja strukturalna (API)
shell/framework/api/requests/<nazwa>_request.py

# Walidacja komend (aplikacja)
shell/application/<bc>/commands/<command>.py  # __post_init__

# Walidacja biznesowa (domena)
shell/domain/<bc>/value_objects/<nazwa>.py     # __post_init__
shell/domain/<bc>/aggregates/<agregat>.py       # guard clauses
shell/domain/<bc>/rules/<nazwa>_rule.py         # Rule Objects
shell/domain/platform/base/specification.py     # Specification base
```

## 3. Podsumowanie — Checklista

Projektując walidację:
- [ ] Każdy poziom ma własne błędy (API → HTTP 422, handler → domenowe)
- [ ] Testy dla każdego poziomu walidacji
