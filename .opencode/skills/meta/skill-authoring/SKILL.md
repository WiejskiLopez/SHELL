---
name: skill-authoring
description: Zasady pisania i edycji skilli — treść wyłącznie twierdząca. Używaj przy tworzeniu nowego skilla, poprawianiu istniejącego lub review'owaniu treści skilli.
---

# Skill Authoring — jak pisać skille

Skill opisuje to, **co robi** dany komponent/mechanizm. Zero wyjątków, zero negacji
w opisach.

## Zasada

- Opisuj **co** byt **robi** — ścieżkę, przepływ, łańcuch obiektów.
- Nie pisz, czego byt **nie robi**. Zamiast „EventHandler nie obsługuje Domain Events"
  napisz: „EventHandler obsługuje Integration Events".
- Opisuj to, co istnieje i co potwierdza kod/testy.

## Sprawdzenie

1. Czytasz opis i widzisz, co byt **robi**?
2. Ktoś frazę „nie/nigdy nie/NIE"? Wyrzuć - przepisz na twierdzenie.
3. Opis prowadzi przez przepływ (obiekt → obiekt), nie przez listę braków.