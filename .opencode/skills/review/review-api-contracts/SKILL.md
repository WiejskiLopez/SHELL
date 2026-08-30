---
name: review-api-contracts
description: Weryfikacja kontraktów API — OpenAPI, tagi i publikacja specyfikacji, wersjonowanie DTO i eventów, format odpowiedzi, konwencje endpointów, walidacja na granicy. Używaj przy code review endpointów i kontraktów konsumowanych przez frontend/inne BC.
---

# Review — Kontrakty API

> API to publiczny kontrakt. Zmiana kontraktu bez wersjonowania to awaria konsumentów.

## 1. OpenAPI i publikacja specyfikacji

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Każdy endpoint opisany tagiem OpenAPI, specyfikacja publikowana dla frontendu | brak tagów / brak publikacji | MEDIUM |
| Specyfikacja generowana z kodu (zgodna z rzeczywistością) | spec pisana ręcznie i rozjechana z implementacją | HIGH |
| `@shell/api-spec` konsumuje opublikowaną spec | backend nie publikuje zmian | HIGH |

Patrz `backend-api-standards`.

## 2. Wersjonowanie i backward compatibility

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Zmiana pól DTO/odpowiedzi wersjonowana | dodano wymagane pole bez wersji/migracji konsumentów | **CRITICAL** |
| Usuwanie pól/endpointów tylko w major version | wycięto pole w minor | **CRITICAL** |
| Dodawanie pól opcjonalnych bezpieczne (bez breaking) | pole dodane jako wymagane → stary klient pęka | HIGH |
| DTO eventów wersjonowane (name, namespace, schema) | event zmieniony bez zmiany wersji | HIGH |

Patrz `dto`, `integration-contracts`.

## 3. Format odpowiedzi i konwencje

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Spójny format odpowiedzi (envelope z id korelacji, itd.) | mieszane formaty 200/201/otwarte body | MEDIUM |
| Poprawne kody HTTP (201 dla tworzenia, 404 dla braku, 409 dla konfliktu) | zapis zwraca 200 zamiast 201; konflikt zwraca 400 | MEDIUM |
| Idempotencja dla mutacji tam, gdzie kontrakt tego wymaga | POST bez idempotency-key dla operacji powtarzalnych | HIGH |
| Brak wycieku wewnętrznych typów (ORM, domeny) w odpowiedzi | pole `updated_at` z ORM lub pełny agregat w body | HIGH |

## 4. Weryfikacja wejścia na granicy

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Wejście walidowane strukturą na API (Pydantic), nie tylko w handlerze | surowe `request.json` wjeżdża do komendy | HIGH |
| Strome typy wejścia (enums przyjmują wartości, nie dowolne stringi) | pole status jako dowolny string | MEDIUM |
| Nadmiarowe/ukryte pola nie ujawniane w OpenAPI | model Pydantic z wewnętrznymi polami | MEDIUM |

Patrz `validation`.

## 5. Konwencje endpointów

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Nazwy zgodne z business capability, nie z klasami technicznymi | endpoint nazwany od tabeli/repo | MEDIUM |
| REST zgodny z zasobami / RPC jawnie nazwany | mieszanka stylów bez zasady | LOW |
| Endpointy grupujące się po BC/zasobach | przypadkowa struktura URL-i | LOW |

Patrz `class-and-type-naming-standards`, `naming-convention-standard`.

## 6. Checklista finalna

- [ ] Spec OpenAPI aktualna i opublikowana.
- [ ] Zmiany DTO wersjonowane, backward compatible.
- [ ] Poprawne kody HTTP i idempotencja.
- [ ] Wejście walidowane na granicy, wyjście nie wycieka wewnętrznych typów.
- [ ] Kontrakt testowany (integration contract test).