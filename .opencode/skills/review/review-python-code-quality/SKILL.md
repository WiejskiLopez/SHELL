---
name: review-python-code-quality
description: Weryfikacja jakości kodu Python — typowanie (mypy strict), organizacja importów, nazewnictwo, prostota i czytelność, złożoność, duplikacja, magic numbers, dead code. Używaj przy code review pod kątem jakości i utrzymywalności kodu.
---

# Review — Jakość kodu Python

> Kod czyta się więcej razy, niż się go pisze. Czystość to funkcja długoterminowej ceny zmiany.

## 1. Typowanie (mypy strict)

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Pełne anotacje typów na sygnaturach publicznych | brak anotacji w API/portach/handlerach | HIGH |
| Brak `Any` / `object` jako ucieczki z typowania | `Any` w kontrakcie domeny | MEDIUM |
| Zero obchodów mypy (`# type: ignore`, untyped def) bez uzasadnienia | `# type: ignore` w kodzie produkcji | HIGH |
| `TypedDict`/dataclass tam, gdzie słownik traci kształt | `dict[str, Any]` jako kontrakt | MEDIUM |

Patrz `arch-test-mypy`.

## 2. Organizacja importów

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Import z modułu definiującego, nie z re-eksportujących `__init__` | import przez `__init__` re-export | MEDIUM |
| Porządek: stdlib → zewnętrzne → lokalne; brak nieużywanych | nieużywany import / zła kolejność | LOW |
| `TYPE_CHECKING` tylko dla typów; brak cykli | cykliczny import | **CRITICAL** |
| Zero wildcard `from x import *` | `import *` w kodzie produkcyjnym | MEDIUM |

Patrz `enterprise-import-conventions`, `import-organization`.

## 3. Nazewnictwo

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Klasy PascalCase + pełna nazwa biznesowa; zero skrótów | `Src`, `Mgr`, `Factory` bez kontekstu | MEDIUM |
| Metody/funkcje snake_case z intencją biznesową | `do_stuff`, `process`, `handle` bez sensu | MEDIUM |
| Zmienne bez skrótów (wyjątki: i, j, e zgodnie z konwencją) | `usr`, `cfg`, `tmp` | LOW |
| ID nazwane biznesowo wg konwencji (PascalCaseId domena / snake_case DB) | `user_idd`, mieszane konwencje | MEDIUM |
| Enumy stanów StrEnum + Value Object, nie nagie stringi | status jako surowy string | HIGH |

Patrz wszystkie skille `naming-standards`.

## 4. Prostota i czytelność

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Brak nadmiarowej złożoności (YAGNI) — kod prostszy, niż potrzebuje | wzorzec wstrzyknięty dla edgy case | MEDIUM |
| Złożoność wg rozsądku — brak metod-ścian (god methods) | handler 200 linii z 5 zadaniami | HIGH |
| Brak magii: stałe nazwane, zero magic numbers | `if x > 86400` zamiast `if age_days > WEEK_IN_SECONDS` | LOW |
| Komentarze tylko tam, gdzie "dlaczego", nie "co" | komentarz dubbingujący linię | LOW |
| `# noqa` z uzasadnieniem, zgodnie z polityką | `# noqa` bez powodu | MEDIUM (patrz noqa-enterprise-policy, architectural-discipline) |

## 5. Duplikacja i martwy kod

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Brak skopiowanej logiki (DRY tam, gdzie to samo znaczenie) | identyczna walidacja w 3 miejscach | MEDIUM |
| Zero dead code / nieużywanych publicznych funkcji | metoda nieużywana nigdzie | LOW |
| Brak nieużywanych zależności/importów | import bez użycia | LOW |

## 6. Pusty fallback i spójność modelowania

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Brak pustych wartości jest "fallbackiem" (`""`, `0`, `[]` jako zastępstwo braku) | `x or ""`, `VO("")`, `[], 0, False` jako default | **CRITICAL** (patrz no-empty-fallbacks) |
| Wartości opcjonalne jawnie `None`, wymagane walidowane | domyślny fallback maskujący bug | HIGH |

## 7. Checklista finalna

- [ ] Mypy strict przechodzi; zero `# type: ignore`/`# noqa` bez uzasadnienia.
- [ ] Imports uporządkowane, zero cykli.
- [ ] Nazwy biznesowe, bez skrótów, enums StrEnum.
- [ ] Brak duplikacji, god-objectów i dead code.
- [ ] Zero pustych fallbacków.