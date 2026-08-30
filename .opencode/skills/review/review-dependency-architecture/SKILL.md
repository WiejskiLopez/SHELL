---
name: review-dependency-architecture
description: Weryfikacja poprawności architektury hexagonalnej/Clean — kierunek zależności między warstwami, granice Bounded Context, package topology, reguły importów, port-adapter i ACL. Używaj przy code review pod kątem struktury warstw i zależności.
---

# Review — Architektura i zależności

> Sprawdzaj zanim cokolwiek innego: błędy strukturalne maskują detale i są najdroższe w naprawie.

## 1. Kierunek zależności (hexagonalna / Clean)

Weryfikuj, czy zależności importowe nie przebijają warstw:

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| `domain` nie importuje `application`, `infrastructure`, API, ORM | `from infrastructure.db import ...` w domenie | **CRITICAL** |
| `application` importuje `domain`, ale nie `infrastructure` | handler importuje adapter bez portu | **CRITICAL** |
| `infrastructure` implementuje porty z `domain`/`application` | adapter importuje port wyłącznie przez `TYPE_CHECKING` jeśli reguła wymaga | MEDIUM |
| Porty (typy zależności) należą do *potrzebującego*, nie do dostawcy | port zdefiniowany w BC dostawcy | CRITICAL |
| Brak importów infrastruktury w domenie nawet w `TYPE_CHECKING` | `if TYPE_CHECKING: from infrastructure...` w domain | **CRITICAL** |

Reguła: domena to liść zależności. Wszystko przez porty/ręce domeny.

## 2. Granice Bounded Context

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| BC nie importuje bezpośrednio wnętrza innego BC | `from billing.repositories import ...` | **CRITICAL** |
| Komunikacja między BC tylko przez porty/DTO/integration events | bezpośrednie wywołanie klasy innego BC | **CRITICAL** |
| Brak współdzielonych repozytoriów między BC | jeden model ORM używany w dwóch BC | HIGH |
| DTO własnością źródłowego BC | DTO zdefiniowane po stronie konsumenta | HIGH |

Patrz `bounded-context-boundary`, `bounded-context-integration`.

## 3. Package topology i platform

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Plik produkcyjny leży we właściwym miejscu (platform / BC / warstwa / bootstrap) | kod domeny w `infrastructure` | HIGH |
| Kod generyczny/prawdziwie platformowy nie duplikuje się per BC | ten sam helper skopiowany do 3 BC zamiast platform | MEDIUM |
| Platform nie wie o konkretnych BC | platform importuje klasę z BC | **CRITICAL** |

Patrz `package-topology`, `platform-boundary`.

## 4. Reguły importów w kodzie

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Import zawsze z modułu definiującego, bez re-exportów | import z `__init__.py` który tylko re-eksportuje | MEDIUM |
| Brak starych `Collection`/`List` z `typing` gdzie wystarcza `list[...]` | przestarzałe typy | LOW |
| `TYPE_CHECKING` tylko dla typów w sygnaturach | runtime'owy import do `if TYPE_CHECKING` w celach innych niż typowanie | MEDIUM |
| Brak cyklicznych importów | moduł A importuje B, B importuje A | **CRITICAL** |

Patrz `enterprise-import-conventions`, `import-organization`.

## 5. Port-adapter i Anti-Corruption Layer

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Port definiuje czarny kontrakt w języku domeny (nie w języku dostawcy) | port nazwany wg zasobów zewnętrznego systemu | HIGH |
| Adapter w infrastrukturze konsumującego BC, nie u dostawcy | adapter ląduje w BC dostawcy | HIGH |
| Nie ma "wycieku" obiektów ORM/HTTP przez port | port zwraca `Model` zamiast domeny/DTO | **CRITICAL** |
| Systemy legacy za ACL z mapowaniem typów | surowe dane zewnętrzne wchodzą do domeny | HIGH |

Patrz `port-adapter`, `port-adapter-structure`.

## 6. Testy architektury jako strażnik

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| `import-linter` pokrywa granice warstw i BC | brak reguły dla nowego modułu | HIGH |
| Testy AST/pytest egzekwują konwencje (entity to nie dataclass, brak ORM w domain) | reguła wyłączona/ignorowana | **CRITICAL** (patrz architectural-discipline) |
| Config zawiera reguły jednocześnie w `select` i `ignore` | sprzeczna konfiguracja | **CRITICAL** |

Patrz `arch-test-import-linter`, `arch-test-mypy`, `arch-test-pytest`, `architectural-discipline`.

## 7. Checklista finalna

- [ ] Domena nie importuje nic poza stdlib/platformą — zero infrastruktury.
- [ ] Handler nie importuje adaptera; tylko port.
- [ ] Migracje wynikają z warstwy infrastruktury, model ORM nie jest domeną.
- [ ] Nie ma współdzielonych tabel/repozytoriów między BC.
- [ ] Arch testy aktywne i przechodzą.