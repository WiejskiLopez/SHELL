---
name: architectural-discipline
description: KARDYNALNA ZASADA — zero wyjątków od reguł architektonicznych i projektowych. Nigdy nie dodawaj `ignore` dla reguł które są w `select`, nigdy nie wycinaj się z reguł architektury, nigdy nie twórz workaroundów zamiast naprawy kodu. TEN SKILL JEST PIERWSZEGO PRIORYTETU — ma pierwszeństwo przed wszystkimi innymi. Każde naruszenie to błąd krytyczny.
---

# ZERO WYJĄTKÓW — kardynalna zasada architektoniczna

> **Nigdy nie wolno dodawać żadnych wyjątków od reguł dobrego projektu i poprawnej architektury. Wszelkie wyjątki to błąd krytyczny.**

---

## 1. Fundamentalna reguła

Każda reguła lintera, każda konwencja architektoniczna, każdy wzorzec projektowy w tym projekcie MUSI być przestrzegany bez wyjątków. Jeśli reguła jest aktywna — kod musi być z nią zgodny. Jeśli reguła nie pasuje do projektu — nie jest włączana.

**Niedopuszczalne wzorce:**

| Praktyka | Dlaczego błąd krytyczny? | Prawidłowo |
|----------|--------------------------|------------|
| `select = ["TCH"]` i `ignore = ["TCH"]` | Reguła jest jednocześnie włączona i wyłączona — to sprzeczność i śmieć w konfiguracji | Albo włącz (usuń z `ignore`) i napraw kod, albo usuń z obu list |
| `ignore = ["E501", "..."]` w `pyproject.toml` | Globalne wyciszanie reguł które są w `select` | Jeśli reguła jest w `select`, kod musi być zgodny; usuń z `select` jeśli nie chcesz jej przestrzegać |
| `# noqa` bez uzasadnienia | Każde `# noqa` to decyzja architektoniczna, nie obejście | `# noqa: <KOD> — <konkretne uzasadnienie>` (zgodnie z noqa-enterprise-policy) |
| Workaround zamiast refaktoryzacji | Maskuje dług techniczny | Napraw kod tak, by spełniał regułę |
| Celowe pomijanie warstwy architektury (np. domain importuje infrastrukturę) | Łamie Clean Architecture | Przestrzegaj kierunku zależności |

## 2. Konsekwencje naruszenia

Każde naruszenie tej zasady jest **błędem krytycznym** i musi być:
1. Natychmiast zgłoszone
2. Naprawione przez usunięcie wyjątku i dostosowanie kodu do reguły (lub usunięcie reguły z konfiguracji jeśli jest nieodpowiednia)
3. Zweryfikowane przez code review

## 3. Relacja z innymi skillami

Ten skill ma **najwyższy priorytet** i nadrzędność nad wszystkimi innymi skillami. W przypadku sprzeczności między zasadą zero-wyjątków a szczegółową regułą z innego skill-a, zasada zero-wyjątków wygrywa.

Inne skille zawierają szczegółowe reguły (np. aggregate-structure, naming-standards, handler-structure) — wszystkie muszą być przestrzegane bez wyjątków.

## 4. Zasada czystej konfiguracji

Pliki konfiguracyjne (`pyproject.toml`, `ruff.toml`, `mypy.ini`, itp.) nie mogą zawierać:
- Reguł jednocześnie w `select` i `ignore` — wybierz jedną opcję
- Wyłączania reguł, które są celowo włączone — napraw kod albo wyłącz regułę całkowicie
- Nieużywanych reguł w `select` — jeśli reguła nie jest potrzebna, nie powinna być w `select`
