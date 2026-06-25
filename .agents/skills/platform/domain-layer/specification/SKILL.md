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

## 2. Specification vs Wyrażenia Warunkowe

| Sytuacja | if/else w kodzie | Specification |
|----------|-----------------|---------------|
| Pojedyncze użycie | OK | Przesada |
| 2+ miejsc użycia | Duplikacja | JEDNO miejsce |
| Łączenie warunków | Zagnieżdżone if | Kompozycja |
| Testowanie | Test przez użycie | Test w isolation |
| Przekazanie do repozytorium | Niemożliwe | Naturalne |

## 3. Podsumowanie — Checklista

Tworząc Specification:
- [ ] Lokalizacja: `shell/domain/<bc>/specifications/`
- [ ] Lokalizacja base: `shell/domain/platform/base/specification.py`
- [ ] Nie ma zależności infrastrukturalnych
- [ ] Testowana w isolation (unit test)
