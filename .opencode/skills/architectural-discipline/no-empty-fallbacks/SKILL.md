---
name: no-empty-fallbacks
description: KARDYNALNA ZASADA — modeluj wartosci jawnie. Wartosci opcjonalne reprezentuj przez None, a wartosci wymagane waliduj bledem.
---

# No Empty Fallbacks — kardynalna zasada

> To najważniejsza reguła w projekcie. Łamanie jej produkuje najtrudniejsze do znalezienia bugi.

## Definicja

**Nigdy nie zastępuj braku wartości pustą wartością.**

Jeśli dana wartość nie została dostarczona:
- **Jest opcjonalna** → `None` (lub odpowiednik w innym języku)
- **Jest wymagana** → rzuć błąd, nie próbuj "ratować" pustym stringiem, zerem, falsem czy pustą listą

## Dlaczego to krytyczne

| Problem | Przykład |
|---------|----------|
| **Ukrywa bugi** | `RepoUrl("")` — wygląda jak poprawny URL, przechodzi testy, ale jest martwy |
| **Maskuje brak danych** | `status or "active"` — ukrywa że nikt nie ustawił statusu |
| **Trudne do debugowania** | Pusta lista zamiast błędu → kod idzie dalej, crash dopiero przy użyciu danych |
| **Niespójność biznesowa** | Pusta wartość biznesowa nie ma sensu — "repozytorium z pustym URL-em" to oksymoron |

## Przykłady — ŹLE vs POPRAWNIE

### 1. VO z opcjonalną wartością

```python
# ŹLE — empty fallback
repo_url=RepoUrl(command.repo_url) if command.repo_url else RepoUrl("")

# POPRAWNIE — None
repo_url=RepoUrl(command.repo_url) if command.repo_url else None

# POPRAWNIE (jeszcze lepiej) — nie ma if w ogóle
repo_url=RepoUrl(command.repo_url)  # RepoUrl akceptuje None
```

### 2. VO z wymaganą wartością

```python
# ŹLE — fallback do pustej wartości
name=WorkflowName(command.name or "")
name=WorkflowName(command.name if command.name else "")

# POPRAWNIE — niech VO zwaliduje i rzuci błąd
name=WorkflowName(command.name)  # rzuci ValueError jeśli puste

# POPRAWNIE — guard clause w handlerze
if not command.name:
    raise ValidationError("name is required")
name=WorkflowName(command.name)
```

### 3. Status/Enum

```python
# ŹLE — domyślny fallback
status = command.status or "active"

# POPRAWNIE — wymuś świadomą decyzję  
status = WorkflowStatus(command.status)  # rzuci błąd jeśli nieznany
```

### 4. Kolekcje

```python
# ŹLE — pusta lista jako fallback
nodes = command.nodes or []

# POPRAWNIE — None jeśli nie ma
nodes = command.nodes  # None → handler wie że nie ma danych

# POPRAWNIE — pusta lista jeśli to legalny stan biznesowy
nodes = command.nodes if command.nodes is not None else []
```

## Kiedy NAPRAWDĘ możesz użyć pustej wartości?

Tylko gdy **pusta wartość ma znaczenie biznesowe**:

```python
# OK — discount=0 to legalna wartość biznesowa (brak rabatu)
discount = Discount(command.discount)  # 0.0 to poprawny Discount

# OK — pusta lista nowych użytkowników to legalny przypadek
new_users: list[UserId] = command.new_users or []
```

Jeśli nie masz 100% pewności że pusta wartość ma znaczenie — użyj `None`.

## Testowanie reguły

Test architektoniczny powinien sprawdzać:

```python
def test_no_empty_fallbacks_in_handlers() -> None:
    """Handler nie może tworzyć pustych VO jako fallback."""
    # Szukaj wzorca: VO("") lub VO(0) lub VO(False)
    # albo: VO(x) if x else VO("")
```

Test kontraktu dla pustych fallbackow pozostaje elementem planu walidacji.

## Wyjątki

**Zero wyjątków.** Jeśli myślisz że to "inny przypadek" — przeczytaj punkt "Dlaczego to krytyczne" jeszcze raz.

## Przykład z projektu (znaleziony i naprawiony)

**Plik:** `shell/project_service/application/project/project/command_handlers/create_project_handler.py`

```python
# PRZED (błąd):
repo_url=RepoUrl(command.repo_url) if command.repo_url else RepoUrl(""),

# PO (poprawne):
repo_url=RepoUrl(command.repo_url) if command.repo_url else None,
```

`RepoUrl("")` tworzyło pozornie poprawny URL który był pusty. Przechodziło testy, kompilowało się, ale w runtime zwracało martwe dane.

> Uwaga: bieżący kod mógł już ewoluować (np. `RepoUrl` przyjmuje `None` i sam rzuca `DomainError`). Zasada pozostaje ta sama — zero pustych fallbacków (`""`, `[]`, `0`, `false`) w miejscu braku wartości.
