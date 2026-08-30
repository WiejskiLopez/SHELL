---
name: review-testing-and-ci
description: Weryfikacja testów i CI — pokrycie wg piramidy, testy round-trip i architektury, jakość testów (bez tautologii), topologia testów, bramki CI (ruff/mypy/pytest), wykonanie run_tests. Używaj przy code review testów i konfiguracji CI.
---

# Review — Testy i CI

> Test, który nie może się nie powieść, to nie test. Bramka, która nie łapie, to fikcja.

## 1. Pokrycie wg piramidy

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Logika domenowa (invarianty, maszyny stanów, VO) pokryta unit testami | reguła biznesowa bez testu | HIGH |
| Mappery z testami round-trip (domain↔model↔DTO) | brak testu odwracalności przy mappingu | HIGH |
| Persystencja/repozytoria pokryte testami integracyjnymi z DB | repo bez testu z realną bazą | MEDIUM |
| Kontrakty integracyjne (HTTP/event) z testami | endpoint zmieniony bez testu kontraktu | HIGH |
| Architektura chroniona testami (import-linter, mypy contracts, AST) | reguły architektury bez strażnika CI | MEDIUM |

Patrz `testing`, `test-topology`, `scope` per `arch-test-*`.

## 2. Jakość testów

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Zero tautologicznych asercji (test przechodzi zawsze) | assert na wartości, którą test sam ustawił | **CRITICAL** |
| Test sprawdza zachowanie, nie implementację | asercja na private field / call sequence | MEDIUM |
| Każdy test niezależny (brak współdzielenia stanu między testami) | testy zależne od kolejności | HIGH |
| Testy odporne (nie chwiejne) — zero flaky bez przyczyny | sleep/time-dependent without control | MEDIUM |
| Brak testów tylko dla pokrycia (bez wartości asercji) | test, który niczego nie weryfikuje | HIGH |

## 3. Topologia testów

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Test we właściwym miejscu (domena / aplikacja / infra / arch / e2e) | test integracyjny w jednostkowych; e2e zbyt wiele | MEDIUM |
| Zasoby testowe (fake, InMemory) we właściwych lokalizacjach | test z komiksami w produkcji | MEDIUM |
| Brak powielania logiki konfiguracji testów per warstwa | setup powtórzony 5x | LOW |

Patrz `test-topology`.

## 4. Fake / InMemory vs mock

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Preferowane prawdziwe implementacje (InMemory, Memorybus), nie mock requirements zbyt szczegółowe | RESTRICTIVE mock `assert_called_once` na każdym kroku | MEDIUM |
| Mocki tylko dla granic, które nie są testowane tutaj | over-mocking wewnętrznych zależności | MEDIUM |
| InMemory repozytorium symetryczne z SQL (kontrakt) | InMemory różne zachowania niż SQL | HIGH |

Patrz `repository-contract-symmetry`.

## 5. CI i narzędzia

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| `run_tests.ps1` wykonuje się bez błędów po zmianie | skrypt nieprzechodzący = niedokończona zmiana | **CRITICAL** (patrz run-tests-validator) |
| CI uruchamia: ruff, mypy strict, import-linter, pytest | reguła narzędziowa poza CI | MEDIUM |
| Brak wyłączania reguł w CI (nie wycinaj się z bramki) | `skip`, `--no-verify`, pomijanie bramki | **CRITICAL** (patrz architectural-discipline) |
| Wersje zależności lockowane | niedeterministyczne buildy | MEDIUM |
| Audyt podatności w CI | brak pip-audit/security check | MEDIUM |

## 6. Checklista finalna

- [ ] Reguły domenowe, mappery i kontrakty pokryte sensownymi testami.
- [ ] Zero tautologicznych asercji; testy niezależne.
- [ ] InMemory symetryczne z SQL.
- [ ] `run_tests.ps1` przechodzi w całości.
- [ ] CI bramkuje ruff, mypy, import-linter, pytest — bez wykluczeń.