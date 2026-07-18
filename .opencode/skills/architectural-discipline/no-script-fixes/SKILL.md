---
name: no-script-fixes
description: KARDYNALNA ZASADA — NIGDY nie naprawiaj plików za pomocą skryptów. Każda zmiana w kodzie produkcyjnym musi być wykonana ręcznie, plik po pliku. Skrypty są dozwolone WYŁĄCZNIE do odczytu/analizy (grep, find, itp.), NIGDY do zapisu/modyfikacji.
---

# NO SCRIPT FIXES — kardynalna zasada

## Definicja

**Nigdy nie używaj skryptów do naprawiania plików produkcyjnych.**

Skrypty (`python -c "... "`, `scripts/*.py`) mogą być używane WYŁĄCZNIE do:
- Analizy kodu (grep, find, wyszukiwanie wzorców)
- Generowania raportów
- Wyświetlania informacji

Skrypty NIGDY nie mogą:
- Modyfikować plików produkcyjnych (`.py`, `.toml`, `.yaml`, itp.)
- Dodawać/usunąć importów
- Zmieniać kolejności parametrów
- Naprawiać błędów składniowych
- Cokolwiek co zapisuje do pliku

## Dlaczego

Każda próba naprawy skryptem:
1. **Łamie składnię** — regex nie ogarnia wszystkich przypadków (CRLF, multiline, różne formaty)
2. **Tworzy nowe błędy** — skrypt naprawia X ale psuje Y i Z
3. **Jest nieprzewidywalna** — nie wiesz co dokładnie skrypt zmienił
4. **Zajmuje więcej czasu** niż ręczna naprawa (debugowanie skryptu + revert + ponowna naprawa)

## Wyjątki

**Zero wyjątków.** Nawet jeśli zmiana jest "prosta" i "mechaniczna" — skrypt ją spieprzy.

## Co zamiast

1. Użyj `grep`/`ruff`/`mypy` żeby znaleźć błędy
2. Otwórz plik w edytorze
3. Popraw ręcznie
4. Zapisz
5. Powtórz dla następnego pliku

## Konsekwencje

Złamanie tej zasady = cofnięcie wszystkich zmian + utrata zaufania. Nie rób tego.
