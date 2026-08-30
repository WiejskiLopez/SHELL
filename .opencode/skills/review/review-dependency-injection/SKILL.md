---
name: review-dependency-injection
description: Weryfikacja DI / Composition Root — struktura modułów DI per BC, lifecycle rejestracji, port-adapter registration, factory dla handlerów, antywzorce (service locator, statyczne fabryki). Używaj przy code review bootstrappingu i rejestracji zależności.
---

# Review — Dependency Injection / Composition Root

> Composition Root to jedyne miejsce, gdzie znane są wszystkie zależności. Rozlewanie go po kodzie to antywzorzec.

## 1. Struktura DI

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Moduły DI per Bounded Context, izolowane interdependencies | jeden wielki moduł DI all-in-one | MEDIUM |
| Przegląd przy bootstrap: warstwy rejestrowane od zależności do zależnych | rejestracja zależona przed jej portem | LOW |
| Brak rejestracji bez użycia (martwe rejestracje) | `providers.Factory` dla klasy nieistniejącej/używanej | MEDIUM |

Patrz `di-composition-root`.

## 2. Port-adapter registration

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Każdy port ma zarejestrowany adapter | port bez implementacji → błąd przy wstrzyknięciu | **CRITICAL** |
| Rejestracja adaptera pod portem, nie pod klasą implementacji | wstrzykiwanie konkretnej klasy zamiast portu | HIGH |
| Jeden port nie ma dwóch sprzecznych adapterów bez wyraźnego wyboru | dwie implementacje rejestrowane pod ten sam port | HIGH |
| Adaptery testowe (InMemory) rejestrowane tylko w testach | InMemory w produkcji | MEDIUM |

Patrz `port-adapter`.

## 3. Lifecycle

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Lifecycle dobrany do natury zależności (singleton/transient/scoped) | singleton zależności transakcyjnej (repo/UoW jako singleton) | **CRITICAL** |
| UoW/transakcje nie-singleton (fresh per request) | współdzielony UoW w singletonie → skażone transakcje | **CRITICAL** |
| Handler bezstanowy rejestrowany jako transient/factory | handler z pamięcią między wywołaniami | HIGH |
| Brak trzymania kontekstu requestu w singletonie | request-scoped dane w singleton | HIGH |

## 4. Antywzorce DI

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Brak Service Locator (kontener w metodzie biznesowej) | `container.resolve(...)` w handlerze | **CRITICAL** |
| Brak statycznych fabryk/globals | `Cache.instance()` zamiast wstrzyknięcia | **CRITICAL** |
| Brak rezerwacji argumentów wprost do konstruktora | wymuszone `**kwargs` bez typu | MEDIUM |
| Factory dla handlerów rejestruje subskrypcje zgodnie z rejestracjami | subskrypcja bez DI Factory | **CRITICAL** (patrz handler-registration-integrity) |

## 5. Testability

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Testy wstrzykują implementation/fake przez konstruktor, nie przez brute-force kontenera | fake montowany przez globalny stan | MEDIUM |
| Zależności jawne w konstruktorze (brak `**kwargs`/`*args` smug) | ukryte zależności w klasie | HIGH |

## 6. Checklista finalna

- [ ] Każdy port ma jeden aktywny adapter produkcji.
- [ ] Lifecycle zgodny z naturą zależności (UoW nie-singleton).
- [ ] Zero Service Locator / statycznych fabryk.
- [ ] Rejestracje handlerów pokryte DI.
- [ ] Testy wstrzykują przez konstruktor.