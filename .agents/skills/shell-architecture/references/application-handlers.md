# Zasady pracy z handlerami aplikacyjnymi

> Uzupełnienie do `application.md` — reguły dotyczące wyłącznie handlerów warstwy aplikacyjnej (command, query i event handlers).

## Zakaz bezpośredniego wołania agregatów innych domen

Handler aplikacyjny **nie może bezpośrednio wołać agregatów, serwisów domenowych, repozytoriów ani żadnych innych elementów** należących do domeny innej niż ta, której dotyczy handler.

### Co wolno?

- Sięgać wyłącznie do agregatów i repozytoriów **własnej domeny** (tej, dla której handler został napisany).
- W przypadku konieczności skorzystania z funkcjonalności **innej domeny** — należy użyć **portu (protokołu)** zdefiniowanego w `application/ports/` lub w domenie docelowej.

### Gdzie implementować adaptery?

Implementacja adaptera dla portu pochodzącego z innej domeny **musi** znajdować się w `infrastructure/` w podkatalogu o nazwie zgodnej z nazwą tej domeny.

Przykład:
- Handler w `shell/application/execution/` potrzebuje funkcjonalności z domeny `platform`
- W `shell/domain/platform/ports/` (lub `shell/application/ports/`) istnieje port (protokół) `PlatformPort`
- Adapter tego portu implementujesz w `shell/infrastructure/platform/`
- Handler wstrzykuje port przez DI — nigdy nie tworzy bezpośrednio instancji agregatu z innej domeny

### Komunikacja poza domenę

To samo dotyczy komunikacji z **elementami spoza systemu domenowego** (np. zewnętrzne API, biblioteki systemowe, bazy danych). Zawsze przez port w warstwie aplikacyjnej/domenowej, z implementacją adaptera w `infrastructure/`.

## Metody wywoływane na agregatach w handlerze

### Tylko metody o nazwie biznesowej

Handler **może wywoływać na agregatach wyłącznie metody, których nazwy wyrażają intencję biznesową** w języku domeny — nigdy metody techniczne.

- ✅ **Dobrze**: `order.confirm()`, `workflow.mark_completed()`, `task.assign_to(user)`, `invoice.cancel()`
- ❌ **Źle**: `order.save()`, `workflow.update()`, `task.merge()`, `invoice.set_status()`, `aggregate.persist()`

Nazwa metody musi mówić **co się dzieje z biznesowego punktu widzenia**, a nie jaką operację techniczną wykonujemy.

### Metody techniczne (`save`, `update`, `merge`, `persist` itp.) są wewnętrzne dla agregatu

Wszelkie metody techniczne, które dotyczą zapisu, scalania, aktualizacji czy synchronizacji stanu — **służą wyłącznie do użytku wewnątrz agregatu**. Nie mogą być wołane przez handler ani żaden inny element zewnętrzny.

Agregat sam zarządza swoim stanem wewnętrznym. Handler jedynie wywołuje metody domenowe (biznesowe), a agregat wewnętrznie (w swojej metodzie biznesowej) wykonuje niezbędne operacje techniczne na swoich polach i za pomocą `append_event()` rejestruje zdarzenia domenowe.

## Nazewnictwo handlerów i eventów — reguła korespondencji

Nazwy klas handlerów i eventów/komend muszą być **biznesowe** i **korespondować ze sobą**.

### Command handlers

Handler komendy **przyjmuje nazwę dokładnie taką samą jak komenda**, tylko z sufiksem `Handler` zamiast `Command`:

- ✅ `StartWorkflowCommand` → `StartWorkflowHandler`
- ✅ `ImportTaskExecutionCommand` → `ImportTaskExecutionHandler`
- ✅ `ArchiveEnvelopeCommand` → `ArchiveEnvelopeHandler`
- ❌ `ImportTaskExecutionCommand` → `ImportTaskFromFileHandler` (inna nazwa biznesowa)
- ❌ `StartWorkflowCommand` → `PrepareWorkflowHandler` (inna nazwa biznesowa)

Handler dla komendy jest **jeden** — jego nazwa zawsze odwzorowuje nazwę komendy.

### Event handlers

Główny handler eventu **przyjmuje nazwę taką samą jak event**, z sufiksem `Handler` zamiast `Event`:

- ✅ `GraphNodeExecutionCompletedEvent` → `GraphNodeExecutionCompletedHandler`
- ✅ `GraphNodeExecutionTimedOutEvent` → `GraphNodeExecutionTimedOutHandler`
- ❌ `GraphNodeExecutionCompletedEvent` → `AdvanceWorkflowOnNodeResultHandler` (brak korespondencji)

Jeśli ten sam event ma **wielu subskrybentów**, **tylko jeden** (główny) przyjmuje nazwę zgodną z eventem. Pozostali mogą mieć nazwy rozszerzone o specyficzne kwalifikatory biznesowe:

- `GraphNodeExecutionCompletedEvent` → `GraphNodeExecutionCompletedHandler` _(główny — przejście workflow)_
- `GraphNodeExecutionCompletedEvent` → `SpawnSubGraphsOnPlannerCompletionHandler` _(drugorzędny — tylko dla węzłów PLANNER)_
- `GraphNodeExecutionCompletedEvent` → `LogAuditHandler` _(drugorzędny — logowanie)_

### Nazwy eventów i komend muszą być biznesowe

Zdarzenia domenowe i komendy opisują **fakty biznesowe** w języku domeny, nie techniczne operacje:

- ✅ `WorkflowCompletedEvent`, `EnvelopeRoutedEvent`, `TaskExecutionCreatedEvent`
- ❌ `GraphNodeStateUpdatedEvent`, `DataSavedEvent`, `ProcessFinishedEvent`

### Dlaczego?

1. **Czytelność** — nazwa handlera od razu mówi, który przypadek użycia realizuje
2. **Łatwość nawigacji** — `Ctrl+Click` z eventu na handler działa intuicyjnie
3. **Konsystencja** — jednakowy wzorzec w całej warstwie aplikacyjnej
4. **Biznesowy język** — kod mówi językiem domeny, nie implementacji
