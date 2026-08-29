---
name: adr-standard
description: "Use when introducing, planning, or changing a future architectural capability: module, package, submodule, or platform area. Mandates Architecture Decision Records in `docs/adr/`, living documentation of implemented state only, and a ban on placeholder directories and prose-only future docs."
user-invocable: false
---

# Standard ADR i planowania przyszłych zdolności

## Cel

Ten skill definiuje sposób, w jaki SHELL planuje i dokumentuje przyszłe zdolności
(capabilities) architektury: nowe moduły, pakiety, podmoduły oraz obszary
platformy. Zastępuje legacy wzorzec plików `doc/TODO.md` opisujących "przyszłą
zawartość katalogu".

Reguła nadrzędna: **planowanie i decyzje dokumentuje się Architecture Decision
Records (ADR). Dokumentacja w drzewie kodu opisuje wyłącznie stan zrealizowany.**
Puste katalogi i proza o przyszłości nie są artefaktem architektury.

## Kiedy używać

Użyj tego skilla, gdy:

- planujesz nowy moduł, podmoduł lub obszar platformy;
- rozważasz przeniesienie granicy pakietowej lub zmiany własności;
- podejmujesz decyzję, czy zdolność ma być elementem platformy czy osobnego podmiotu;
- chcesz opisać przyszłą funkcjonalność, która jeszcze nie istnieje;
- przeglądasz istniejące placeholder-y, puste katalogi lub starsze dokumenty
  "przyszłej zawartości".

## Obowiązkowe zasady

1. **Przyszła zdolność = ADR, nie plik w drzewie kodu.** Każda decyzja o nowej
   granicy, module lub obszarze musi mieć rekord decyzji architektonicznej.
2. **Zakaz placeholder-ów.** Nie twórz pustych katalogów modułów (np.
   `domain/`, `application/`, `infrastructure/`) ani katalogów `doc/`
   z samym opisem przyszłej zawartości.
3. **Zakaz dokumentów "przyszłej zawartości".** Pliki `TODO.md`, "Future concept",
   "przyszłe pliki", "przyszłe przepływy" i im podobne nie mają prawa istnieć
   w źródłach ani w dokumentacji katalogów.
4. **Living documentation opisuje realny stan.** Dokumentacja (np.
   `shell/platform/doc/`) opisuje wyłącznie kod, który istnieje i działa.
   Zmiana kodu wymaga aktualizacji dokumentu; dokument nie wyprzedza kodu.
5. **Moduł powstaje z kodem i testami albo nie powstaje.** Nowy moduł należy
   tworzyć jako szkielet z działającym kodem i testami (zob. `scaffold-aggregate`),
   a nie jako strukturę katalogów z pustą dokumentacją.
6. **ADR to źródło prawdy o granicach.** Umiejscowienie (platforma vs własny
   moduł vs BC), własność i reguły importów rozstrzyga się w ADR przed
   implementacją, zgodnie z `package-topology`, `platform-boundary` i
   `bounded-context-boundary`.

## Lokalizacja ADR

Każdy ADR żyje pod ścieżką:

```text
docs/adr/NNNN-<krotki-opis>.md
```

- `NNNN` — kolejny numer rekordu (0001, 0002, ...);
- `<krotki-opis>` — identyfikator tematu w `snake_case`.

## Struktura ADR

```markdown
# ADR-NNNN: <decyzja>

## Status

<Proposed | Accepted | Superseded | Deprecated>

## Data

<YYYY-MM-DD>

## Kontekst

<Problem i fakty, które uzasadniają decyzję. Tylko stan faktyczny,
bez życzeń.>

## Decyzja

<Co dokładnie postanawiamy. Jednoznacznie, bez wariantów.>

## Konsekwencje

<Pozytywne i negatywne skutki, wymagana migracja, wpływ na istniejące
mechanizmy i dokumentację.>
```

## Procedura

1. Sformułuj problem i fakty (kontekst).
2. Porównaj opcje według istniejących reguł: `package-topology`,
   `platform-boundary`, `bounded-context-boundary`, konwencji BC.
3. Zapisz ADR w `docs/adr/` i oznacz jego status.
4. Nie twórz pustych katalogów ani dokumentów przyszłości w drzewie kodu.
5. Gdy zdolność wchodzi do implementacji, twórz szkielet z kodem i testami
   w miejscu wskazanym przez ADR.
6. Po każdej zmianie realizowanego kodu zaktualizuj living documentation
   (stan faktyczny).

## Walidacja

ADR nie jest walidowany kompilatorem. Walidacja jest dwupoziomowa:

- **architektoniczna** — decyzja w ADR musi być zgodna z `package-topology`,
  `platform-boundary` i `bounded-context-boundary`;
- **logiczna** — agent AI sprawdza, czy ADR jest jednoznaczny, czy wskazuje
  realny stan faktyczny, i czy nie wprowadza placeholder-ów ani deklaracji
  nieistniejącej implementacji.

Wynik walidacji może być wyłącznie:

- `ZGODNE Z ARCHITEKTURA` — decyzja spójna z regułami i stanem faktycznym;
- `BLAD ARCHITEKTONICZNY` — raport wskazuje problem; poprawka wymaga albo
  zmiany ADR, albo uzasadnionej zmiany reguł, nigdy obejścia reguł.

## Czego nie robić (legacy anti-patterns)

- nie twórz `doc/TODO.md` ani `doc/FUTURE.md` opisujących przyszłą zawartość;
- nie twórz pustych katalogów modułu jako "rezerwacji" obszaru;
- nie pisz "zaraz dodamy", "do uzupełnienia", "future work" w dokumentacji
  katalogów i Wiki;
- nie deklaruj, że funkcjonalność istnieje, zanim istnieje kod i testy;
- nie trzymaj backlogu ani planów w źródłach i dokumentacji pakietów.

## Minimalny szablon

```markdown
# ADR-NNNN: <decyzja>

## Status

<Proposed | Accepted | Superseded | Deprecated>

## Data

<YYYY-MM-DD>

## Kontekst

<stan faktyczny>

## Decyzja

<jednoznaczne postanowienie>

## Konsekwencje

<skutki i wymagania>
```