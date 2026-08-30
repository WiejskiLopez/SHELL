---
name: review-security
description: Weryfikacja bezpieczeństwa aplikacji — sekrety, uwierzytelnianie i autoryzacja, walidacja wejścia, wstrzykiwanie, ekspozycja danych, IDOR, SSRF, podatności zależności. Używaj przy każdej zmianie obsługującej dane/sieć — ustalenia z tego skilla mają najwyższe severity.
---

# Review — Bezpieczeństwo

> Bezpieczeństwo nie jest funkcją, jest warunkiem wstępnym. Tutaj każda wada ma wagę BLOCKER/CRITICAL.

## 1. Sekrety i konfiguracja

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Brak sekretów w kodzie, konfiguracji i repozytorium (`.env` w git) | hasło/api key/token w źródle lub commicie | **BLOCKER** |
| Sekrety z vault/env zmiennych, nigdy w kodzie | defaultowy secret w kodzie | **BLOCKER** |
| Brak sekretów w logach i komunikatach błędów | wyjątek rzucający pełny connection string | **BLOCKER** |
| `.gitignore` chroni pliki sekretów | brak wpisu `.env*` | HIGH |

## 2. Uwierzytelnianie i autoryzacja

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Każdy endpoint mutujący sprawdza uprawnienia na granicy aplikacji | autoryzacja w domenie albo brak sprawdzenia | **BLOCKER** |
| Idempotentna kontrola dostępu do zasobu (IDOR) — owner check | dostęp po ID bez weryfikacji właściciela | **BLOCKER** |
| Brak ufności do pól przychodzących jako tożsamość | `user_id` z requestu traktowany jako zalogowany użytkownik | **BLOCKER** |
| Rola/uprawnienia nie pochodzą z danych bagietki | rola z DB podatna na niejawne eskalacje | HIGH |
| Wszystkie publiczne ścieżki świadomie oznaczone | endpoint niejawnie publiczny | HIGH |

## 3. Walidacja wejścia i wstrzykiwanie

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Wejście walidowane strukturą (Pydantic) na granicy API | surowy `request.json` do komend | HIGH |
| Zero wstrzykiwania SQL (ORM/query builder, nie f-string do SQL) | SQL budowany f-stringiem | **BLOCKER** |
| Zero deserializacji z pól niezaufanych z funkcjami (yaml.load unsafe, pickle) | `yaml.load`/`pickle`/`eval` na danych wejściowych | **BLOCKER** |
| Path traversal zablokowane (normalizacja ścieżek) | `os.path.join` na nazwie z requestu | **BLOCKER** |
| Dane wyjściowe escapowane/serializowane bezpiecznie (XSS) | zwracanie surowego HTML w kontrakcie | HIGH |

Patrz `validation`.

## 4. Ekspozycja danych

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Brak wycieku poufnych pól (hasła, tokeny, PII) w DTO/API/logach | pole `password` lub `api_key` w DTO odpowiedzi | **BLOCKER** |
| Modele serializacji mapują jawne pola, nie `dict(model.__dict__)` | **dict__**/`model_dump()` z wewnętrznymi polami | HIGH |
| Brak ekspozycji wewnętrznych komunikatów błędów bezpieczeństwa | szczegół błędu (stack) w odpowiedzi | MEDIUM |

## 5. Zewnętrzne zasoby i zależności

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Brak SSRF (walidacja adresów URL; whitelist hostów) | fetch na dowolny URL z parametru | **CRITICAL** |
| Zależności aktualizowane, audyt podatności (pip-audit etc.) w CI | znana CVE w locked dependency | HIGH |
| TLS na połączeniach wychodzących | HTTP bez TLS | HIGH |
| Rate limiting na ścieżkach wrażliwych | brak limitu na login/rejestrację | MEDIUM |

## 6. Checklista finalna

- [ ] Zero sekretów w kodzie/logach/git.
- [ ] Autoryzacja i owner-check na każdej mutacji.
- [ ] Zero dynamicznego SQL / niebezpiecznej deserializacji.
- [ ] DTO bez pól wrażliwych, jawne mapowanie.
- [ ] Audyt zależności; brak znanych CVE.