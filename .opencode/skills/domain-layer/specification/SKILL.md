---
name: specification
description: Wzorzec Specification (Specyfikacja) w DDD — komponowalne reguły biznesowe, walidacja, filtrowanie w repozytoriach. Używaj gdy potrzebujesz wielokrotnego użytku reguł biznesowych, łączenia warunków (AND/OR/NOT) lub przekazywania filtrów do repozytorium.
---

# Specification Pattern w Enterprise DDD

> **Status wzorca:** test architektury `test_domain_structure__test_specifications_extend_specification` wymaga, by specyfikacje dziedziczyły po bazie `Specification`. Ta baza **nie istnieje jeszcze w platformie** — wprowadzenie wzorca wymaga najpierw utworzenia `shell/platform/domain/base/specification.py`. Do tego czasu stosuj guard clauses i repozytoria `list_by_*` (patrz `pattern-standards/guard-clause-pattern`).

## 1. Czym jest Specification

Specification to **komponowalny predykat biznesowy** — hermetyzuje pojedynczą regułę biznesową w osobnej klasie. Pozwala na:

- **Wielokrotne użycie** reguł biznesowych
- **Kompozycję** reguł (AND, OR, NOT)
- **Filtrowanie** w repozytoriach (specification → SQL WHERE)
- **Walidację** obiektów domenowych

## 2. Podsumowanie — Checklista

Tworząc Specification:
- [ ] Lokalizacja: `shell/<service>/domain/<bc>/aggregates/<agregat>/specifications/`
- [ ] Lokalizacja base: `shell/platform/domain/base/specification.py` (wzorzec docelowy — wymaga wdrożenia)
- [ ] Specyfikacja korzysta z czystych typow domenowych
- [ ] Testowana w isolation (unit test)
