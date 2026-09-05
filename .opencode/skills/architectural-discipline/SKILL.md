---
name: architectural-discipline
description: KARDYNALNA ZASADA — zero wyjątków od reguł architektonicznych i projektowych oraz ZERO KOMPROMISÓW. Nigdy nie dodawaj `ignore` dla reguł które są w `select`, nigdy nie wycinaj się z reguł architektury, nigdy nie twórz workaroundów zamiast naprawy kodu, nigdy nie akceptuj odstępstwa pod hasłem „zysk w stosunku do efektu mały". Konstrukcja niespełniająca standardu enterprise jest defektem i wymaga natychmiastowej refaktoryzacji. TEN SKILL JEST PIERWSZEGO PRIORYTETU — ma pierwszeństwo przed wszystkimi innymi. Każde naruszenie to błąd krytyczny.
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

Inne skille zawierają szczegółowe reguły (np. `aggregate-structure`, `aggregate-design`, `handler-structure`, `naming-convention-standard`) — wszystkie muszą być przestrzegane bez wyjątków.

## 4. Zasada czystej konfiguracji

Pliki konfiguracyjne (`pyproject.toml`, `ruff.toml`, `mypy.ini`, itp.) nie mogą zawierać:
- Reguł jednocześnie w `select` i `ignore` — wybierz jedną opcję
- Wyłączania reguł, które są celowo włączone — napraw kod albo wyłącz regułę całkowicie
- Nieużywanych reguł w `select` — jeśli reguła nie jest potrzebna, nie powinna być w `select`

## 5. Zero kompromisów architektonicznych

### 5.1 Konformizm jest predykatem binarnym

Zgodność konstrukcji ze standardem architektonicznym jest **binarna**: konstrukcja albo
spełnia standard w całości, albo jest **defektem**. Nie istnieje stan „akceptowalnego
odstępstwa", „rozsądnego skrótu" ani „wystarczająco dobrego". Każda konstrukcja, która
nie spełnia standardu, jest technicznie wadliwa i kwalifikuje się do natychmiastowej
refaktoryzacji do stanu docelowego.

### 5.2 Kryterium decyzyjne

Jedynym kryterium oceny konstrukcji jest **standard enterprise** (reguły warstw,
wzorce, konwencje nazw, kontrakty, dyscyplina zależności, jawność decyzji). Niedozwolone
są jako uzasadnienie odstępstwa:

- „zysk w stosunku do nakładu jest mały" — koszt implementacji nie unieważnia wymogu;
- „taka jest konwencja w repozytorium / tak już było" — konwencja jest zmieniana, gdy
  standard definiuje lepszą strukturę; przyzwyczajenie nie jest argumentem;
- „działa, więc zostaje" — działanie funkcjonalne nie jest dowodem zgodności strukturalnej;
- „legacy / out of scope / później" — dług techniczny nie jest planem;
- „minimalizacja churnu / ryzyka" — to uzasadnienie zarządcze, nie architektoniczne;
  nie może determinować kształtu rozwiązania.

### 5.3 Obowiązek natychmiastowej refaktoryzacji

Konstrukcja niespełniająca standardu jest **defektem i musi zostać zrefaktoryzowana
natychmiast**, w ramach bieżącej pracy — nie „zaplanowana", nie „udokumentowana i
przesunięta", nie „zaakceptowana jako kompromis". Odroczenie dopuszczalne wyłącznie
w formie **formalnego ADR zaakceptowanego przez właściciela architektury**, który
jednoznacznie klasyfikuje pozycję jako dług i wyznacza termin spłaty. ADR nie czyni
defektu „poprawnym" — czyni go jawnym i kontrolowanym.

### 5.4 Zakaz decyzji ukrytych

Każde odstępstwo od zatwierdzonego designu musi być **jawne**: udokumentowane w ADR z
powodem i akceptacją. Odstępstwo **ciche** (bez zapisu) jest błędem krytycznym — jest
nierozróżnialne od błędu implementacyjnego i nie podlega review. Jawność odstępstwa jest
warunkiem jego legalności, a nie łagodzenia.

### 5.5 Obowiązek zapytania przed odstępstwem

Jeżeli konstrukcja **mogłaby być odstępstwem** od standardu:

1. **ZAPYTAJ właściciela architektury PRZED wykonaniem** — nie podejmuj decyzji
   jednostronnie i nie „cicho poprawiaj".
2. **POINFORMUJ, że wariant niezgodny jest złą decyzją** — przedstaw standard i
   konsekwencje odstąpienia.
3. Wykonaj wariant niezgodny **WYŁĄCZNIE po jawnej akceptacji** właściciela.
4. Po akceptacji:
   - oznacz konstrukcję jako **świadome legacy** (komentarz/oznaczenie w kodzie i dokumentacji);
   - zapisz **lepsze rozwiązanie w ADR** — z opisem stanu docelowego i terminem spłaty.
5. Bez akceptacji odstępstwo **nie istnieje** — wykonuj wariant zgodny ze standardem.

Odwrotna zasada: „poprawka cicha" względem zatwierdzonej specyfikacji (zmiana, której
specyfikacja nie nakazała) również wymaga zapytania — nawet jeśli autor uważa ją za
lepszą. Specyfikacja zmienia się tylko przez jawną aktualizację lub ADR.

### 5.6 Spójność specyfikacji i implementacji

Dokument projektowy (specyfikacja) i kod muszą być **zgodne co do stanu docelowego**.
Gdy zachodzi rozbieżność:

- jeśli **specyfikacja jest błędna** (łamie standard) → popraw specyfikację;
- jeśli **kod jest błędny** (nie spełnia specyfikacji) → refaktoryzuj kod;
- **nigdy nie pozostawiaj** rozbieżności między nimi jako „stanu przejściowego" bez
  jawnej noty.

### 5.7 Testy

Każda refaktoryzacja wymaga potwierdzenia przez pełną weryfikację (testy warstwy,
testy architektury, linter, type checker, reguły zależności). Konstrukcja uznawana jest
za zgodną wyłącznie, gdy weryfikacja jest w całości zielona.
