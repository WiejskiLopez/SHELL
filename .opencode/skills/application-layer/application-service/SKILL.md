---
name: application-service
description: Zasady projektowania Application Services / Use Cases w architekturze hexagonalnej — granica między aplikacją a domeną, koordynacja transakcji, autoryzacja, walidacja wejściowa, mapowanie na DTO. Używaj gdy projektujesz nowy Use Case, refaktoryzujesz handler, albo potrzebujesz granicy między aplikacją a domeną.
---

# Application Service / Use Case w Enterprise DDD

## 1. Application Service to Handler

W tej architekturze **Command Handler** i **Query Handler** pełnią rolę Application Services. Każdy Use Case to jeden handler.

## 2. Odpowiedzialność Application Service

Application Service **koordynuje**, ale nie zawiera logiki biznesowej. Jego odpowiedzialność:

1. **Odebranie komendy** (DTO)
2. **Mapowanie na obiekty domenowe** (przez mapper)
3. **Autoryzacja** (sprawdzenie uprawnień)
4. **Walidacja wejściowa** (strukturalna — typy, formaty)
5. **Koordynacja domeny** (wywołanie agregatów/usług)
6. **Zarządzanie transakcją** (UoW)
7. **Mapowanie wyniku na DTO** (dla query)

## 3. Application Service Nie Zawiera Logiki Biznesowej

Jeśli w handlerze pojawia się **if/else** z regułami biznesowymi → przenieś do Domain Service lub agregatu.

## 4. Transaction Script vs Domain Model

| Sytuacja | Domain Model | Transaction Script |
|----------|-------------|-------------------|
| Bogata logika biznesowa | Tak | Nie |
| Prosty CRUD | Nie | Tak (QueryService) |
| Złożone reguły | Tak (agregat + service) | Nie |
| Performance zapisu | Umiarkowany | Wysoki |

## 5. Autoryzacja w Application Service

Autoryzacja jest sprawdzana na poziomie aplikacji, zanim logika domenowa zostanie uruchomiona.

```python
class DeleteExecutionHandler:
    def __init__(self, authorization_service: AuthorizationService, repository: ExecutionRepository, unit_of_work: UnitOfWork) -> None:
        ...

    async def handle(self, command: DeleteExecutionCommand) -> None:
        self._authorization_service.assert_can_delete(command.user_id, command.execution_id)
        async with self._unit_of_work:
            execution = await self._repository.get(ExecutionId(command.execution_id))
            execution.delete()
            await self._repository.save(execution)
            self._unit_of_work.stage_events(execution.pull_events())
```

## 6. Application Service a Testy

Testy Application Services używają InMemory implementacji — testują koordynację, nie logikę biznesową.

## Dodatkowe reguły dla Command Handlerów

W tym projekcie Command Handler (Application Service dla komend) podlega rygorystycznym regułom:
- Modyfikuje **max jeden agregat** domenowy.
- Ładuje agregat z repozytorium, dostarcza mu dane przez serwisy domenowe (porty w module agregatu), woła metodę agregatu z kompletem parametrów.
- **Zero decyzji biznesowych** — brak `if/else`, brak wyboru między ścieżkami.
- Zapis + eventy w tej samej transakcji.

> Szczegółowe reguły struktury → [command-handler-structure](../../pattern-standards/command-handler-structure/SKILL.md)

## 7. Podsumowanie — Checklista

Projektując Application Service (Handler):
- [ ] Jeden Use Case = jeden handler
- [ ] Handler koordynuje, nie zawiera logiki biznesowej
- [ ] Logika biznesowa w agregacie / Domain Service
- [ ] Walidacja wejściowa przed przekazaniem do domeny
- [ ] Autoryzacja sprawdzana przed operacją
- [ ] Testy z InMemory implementacjami
