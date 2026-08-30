---
name: review-application-layer
description: Weryfikacja warstwy aplikacji — command/query handler, use case, DTO, mapper, walidacja, CQRS, UoW, rejestracja handlerów. Używaj przy code review handlerów i granicy aplikacja/domain.
---

# Review — Warstwa aplikacji

> Aplikacja koordynuje, nie myśli. Wszelka logika biznesowa w handlerze to naruszenie.

## 1. Command / Query handlers

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Handler bez logiki biznesowej — tylko koordynacja | kalkulacja/decyzja w handlerze zamiast delegacji do agregatu/serwisu | **CRITICAL** |
| Query handler jest read-only, zwraca DTO, nie mutuje stanu | query robi zapis | **CRITICAL** |
| UoW jako async context manager, `stage_events()` przed commita | commit/`add()` rozrzucone w handlerze | HIGH |
| Handler nie importuje adapterów; zależy od portów | `from infrastructure...` w handlerze | **CRITICAL** |
| Handler ma jedno zadanie (single command/query) | handluje dwie komendy | MEDIUM |
| `TYPE_CHECKING` dla portów w sygnaturach | runtime'owy import portu | LOW |

Patrz `command-handler`, `handlers`, `command-handler-structure`, `handler-structure`, `query-handler-structure`.

## 2. DTO i mapper

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| DTO to frozen dataclass, typy proste, zero logiki biznesowej | DTO z metodami/metodykami | HIGH |
| DTO własnością domeny/BC, która je produkuje | DTO zdefiniowane po stronie konsumenta | HIGH |
| Mapper symetryczny — round-trip mapping bez utraty danych | `to_dto` nie daje się odwrócić; test round-trip brakuje | **CRITICAL** |
| Mapper bez logiki biznesowej | mapper liczy coś mimo mapowania | HIGH |
| DTO nie zawiera pól technicznych/ORM | `updated_at` ORM w DTO kontraktowym bez potrzeby | MEDIUM |

Patrz `dto`, `data-transfer-object-structure`, `mapper`, `mapper-structure`.

## 3. Walidacja — trzy warstwy

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Walidacja strukturalna (typ/reakcje/pola) na granicy API (Pydantic) | walidacja strukturalna rozsiana po handlerach | HIGH |
| Walidacja biznesowa (invarianty) w domenie, nie w API | business rule w Pydantic | **CRITICAL** |
| Walidacja aplikacyjna (uprawnienia, koordynacja) w handlerze | autoryzacja w domenie | MEDIUM |
| Brak pustych fallbacków przy mapowaniu komend | `command.field or default` | **CRITICAL** (patrz no-empty-fallbacks) |

Patrz `validation`, `validation-layers-pattern`.

## 4. CQRS read/write

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Read model odseparowany od write model | query czyta domenę/agregaty bezpośrednio | HIGH |
| QueryService / read model wykonuje optymalne zapytania (materialized view, projections) | query leci po ORM z ekspozycją domeny | MEDIUM |
| Eventual consistency akceptowana świadomie | handler czeka/retry synchronizując read na write | MEDIUM |

Patrz `cqrs`.

## 5. Rejestracja handlerów

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Każdy `.subscribe()`/`.register()` w fabryce ma odpowiadający `providers.Factory()` w kontenerze | handler zarejestrowany bez DI | **CRITICAL** (patrz handler-registration-integrity) |
| Duplikacja rejestracji / brak rejestracji | command bez handlera → błąd runtime | HIGH |
| Żaden event/command nie ma dwóch handlerów o sprzecznych skutkach | dwa handlery na ten sam event z różną logiką | HIGH |

## 6. Checklista finalna

- [ ] Zero logiki biznesowej w handlerach (decyzje w domenie).
- [ ] Query handlery nie mutują stanu.
- [ ] DTO frozen, mappery z testami round-trip.
- [ ] Walidacja na właściwych warstwach.
- [ ] Każda rejestracja ma DI Factory.