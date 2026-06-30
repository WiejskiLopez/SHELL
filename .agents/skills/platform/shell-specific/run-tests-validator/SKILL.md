---
name: run-tests-validator
description: >
  Ostateczny wyrocznia poprawności — run_tests.ps1 musi wykonać się bez błędów.
  Używaj przy każdej zmianie kodu, refaktoryzacji, naprawie błędów.
  Gdy skrypt nie przechodzi — nie zakładaj że wiesz co robić,
  zawsze pokaż userowi co się stało i zapytaj o decyzję.
---

# Reguła walidacji przez `run_tests.ps1`

## Zasada nadrzędna

**Żadna zmiana nie jest poprawna, dopóki `.\run_tests.ps1` nie wykona się w całości bez błędów.**

Skrypt uruchamia wszystkie testy, lintery, type checker i audyty bezpieczeństwa.
Jeśli którykolwiek krok zwróci błąd (a nie jest oznaczony jako `-AllowFailure`), zmiana jest niekompletna.

## Co robić gdy skrypt nie przejdzie

1. **Nie naprawiaj automatycznie** — pokaż userowi:
   - który krok skryptu się wysypał
   - jakie są błędy w konsoli (fragment)
   - twoją propozycję naprawy (krótko)

2. **Poczekaj na odpowiedź** — user decyduje czy:
   - zaakceptować twoją propozycję
   - zaproponować inne podejście
   - tymczasowo pominąć problem

## Co NIE jest wyrocznią

- Pojedyncze testy jednostkowe — mogą przechodzić nawet gdy reszta walidacji pada
- `ruff check shell/` — to tylko lint, nie całościowa walidacja
- Subiektywne odczucie że "to na pewno działa"
