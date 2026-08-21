---
name: specification
description: Wzorzec Specification (Specyfikacja) w DDD — komponowalne reguły biznesowe, walidacja, filtrowanie w repozytoriach. Używaj gdy potrzebujesz wielokrotnego użytku reguł biznesowych, łączenia warunków (AND/OR/NOT) lub przekazywania filtrów do repozytorium.
---

# Specification Pattern w Enterprise DDD

## 1. Czym jest Specification

Specification to **komponowalny predykat biznesowy** — hermetyzuje pojedynczą regułę biznesową w osobnej klasie. Pozwala na:

- **Wielokrotne użycie** reguł biznesowych
- **Kompozycję** reguł (AND, OR, NOT)
- **Filtrowanie** w repozytoriach (specification → SQL WHERE)
- **Walidację** obiektów domenowych

## 2. Podsumowanie — Checklista

Tworząc Specification:
- [ ] Lokalizacja: `shell/domain/<bc>/aggregates/<agregat>/specifications/`
- [ ] Lokalizacja base: `shell/domain/platform/base/specification.py`
- [ ] Specyfikacja korzysta z czystych typow domenowych
- [ ] Testowana w isolation (unit test)
