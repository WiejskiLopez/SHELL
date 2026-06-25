# Antywzorce — wyuczone na awariach tego kodu

Każdy antywzorzec pochodzi z realnej analizy błędów logicznych w projekcie SHELL. Format: **co poszło nie tak → dlaczego to boli → prawidłowy wzorzec**. Czytaj ten plik, gdy modyfikujesz relacje między agregatami, dodajesz pole persystowane, albo refaktoryzujesz warstwy.

---

## 1. Refaktoryzacja relacji bez lockstepu warstw

**Co poszło nie tak.** Odwrócono kierunek asocjacji `Workflow ↔ TaskExecution` (Workflow traci `task_execution_id`, za to TaskExecution/GraphExecution zyskują `workflow_id`). Zmieniono agregat, ale **nie zaktualizowano** mapperów aplikacyjnych ani handlerów. Skutek: `AttributeError` w `workflow_to_dto` przy każdym odczycie property, które już nie istnieje; pole `task_execution.workflow_id` nigdy nieustawiane w produkcji, więc reverse-lookup zwraca zawsze `None`.

**Dlaczego to boli.** Refaktoryzacja asocjacji dotyka wielu warstw naraz. Jeśli dotkniesz tylko jednej, pozostałe pracują na starym modelu danych i ciszą lub wyjątkiem runtime.

**Prawidłowy wzorzec.** Przy każdej zmianie pola agregatu persystowanego dotknij **wszystkich 6 miejsc** w jednym commicie:
1. agregat domeny (slot, property, `__init__`, ew. metoda domenowa),
2. SQL model ORM (kolumna),
3. mapper SQL w obu kierunkach (`*_model_to_entity` i `*_entity_to_model`),
4. InMemory repo (jeśli zmienia semantykę lookupów),
5. mapper DTO aplikacyjny (`*_to_dto`),
6. handlery produkcyjne (ustawiają nowe pole przy tworzeniu agregatu).

Jeśli punkt 6 pominięty — pole zawsze `None`, reverse-lookup martwy. Patrz też checklist *Mapper symmetry* i *Lockstep* w `checklists.md`.

---

## 2. Warunkowa emisja eventów przejścia stanu

**Co poszło nie tak.** `Workflow.finish(now, task_execution_id=None)` emituje `WorkflowCompletedEvent` tylko `if task_execution_id is not None`. Handler joina woła `workflow.finish(now)` bez argumentu → event nie wyemitowany → `CrownSchedulerHandler` (subskrybowany na ten event) nigdy nie obudzony → parent-graph z joinem **utknął na zawsze**.

**Dlaczego to boli.** Event reprezentuje fakt przejścia stanu agregatu (`running → done`). To przejście zdarzyło się niezależnie od tego, czy optional `task_execution_id` został przekazany. Warunkowanie emisji od parametru rozdziela maszynę stanów od powiadomień — sagi nigdy się nie dowiadają, że stan się zmienił.

**Prawidłowy wzorzec.** Emisja eventu przejścia stanu jest **bezwarunkowa**. Parametry opcjonalne trafiają do payloadu eventu, ale nie decydują o tym, czy event powstanie:

```python
def finish(self, *, now, task_execution_id=None) -> None:
    self._status = Status.done()
    self.append_event(WorkflowCompletedEvent.now(self.id, task_execution_id, now=now))
```

---

## 3. Niejednoznaczne lookupy po współdzielonym kluczu

**Co poszło nie tak.** `graph_executions.get_by_task_execution_id(...)` z założenia zwraca jeden graf. Ale sub-GraphExecution współdzieli `task_execution_id` z parentem. Po otwarciu pierwszego sub-grafa istnieje wiele GraphExecution z tym samym `task_execution_id` → SQL rzuca `MultipleResultsFound`, in-memory zwraca losowy pierwszy.

**Dlaczego to boli.** Współdzielony FK nie jest unikalnym identyfikatorem zasobu. Lookup po nim jest z definicji niejednoznaczny, gdy tylko pojawi się drugi rekord z tą samą wartością.

**Prawidłowy wzorzec.** Lookup zasobu po ID jego właściciela (np. `get_by_workflow_id(event.workflow_id)` zamiast `get_by_task_execution_id`). Jeśli event niesie kilka identyfikatorów, wybierz ten, który jest unikalny dla szukanego zasobu. Gdy nieuniknione zwrócenie kolekcji — obsługuj jawnie `list[X]`, nigdy nie zakładaj `[0]` bez `order_by` (patrz antywzorzec 9).

---

## 4. Model ORM rozjedżony ze schematem bazy

**Co poszło nie tak.** Model ORM `GraphExecutionModel` ma kolumnę `workflow_id` i zwykły index zamiast unique po `task_execution_id`. Ale najnowsza migracja Alembic **nadal dodaje** `parent_tasker_node_execution_id` i **nie dodaje** `workflow_id`. Po `alembic upgrade head` na istniejącej bazie: `OperationalError: no such column: workflow_id`.

**Dlaczego to boli.** SQLAlchemy zakłada, że schemat bazy pasuje do modelu. Rozjazd objawia się dopiero w runtime, przy pierwszym zapisie/odczycie kolumny której nie ma.

**Prawidłowy wzorzec.** Każda zmiana modelu ORM wymaga migracji Alembic w tym samym PR. Przy review sprawdź, że `models/*.py` i `migrations/sql/versions/*.py` są zgodne — kolumna-dla-kolumny, index-dla-indexu. Szczególnie przy usuwaniu kolumn: model usuwa, migracja też musi usunąć (+ drop constraint/index).

---

## 5. Hardcoded regression po usunięciu source pola

**Co poszło nie tak.** Po usunięciu `workflow.task_execution_id` env builder subprocessa dostał `"SHELL_TASK_EXECUTION_ID": ""` zamiast pobrania z `graph_execution.task_execution_id` (które jest dostępne kilka linii wyżej). Subprocesy tracą identyfikator taska — audyt, logowanie i routing wewnętrzny przestają działać.

**Dlaczego to boli.** Gdy usuwasz źródło jakiejś wartości, każdy konsument tej wartości zostaje z pustym placeholderem. Hardcoded `""`/`None`/`[]` ukrywa błąd — kompiluje się, przechodzi testy składniowe, ale jest martwy funkcjonalnie.

**Prawidłowy wzorzec.** Po usunięciu pola znajdź wszystkich konsumentów (`grep`) i zapewnij im nowe źródło danych. Często to samo ID jest dostępne w sąsiednim obiekcie w zakresie. Nigdy nie zastępuj hardcoded defaultem tylko po to, by kod się kompilował.

---

## 6. Adapter asymmetry — InMemory no-op vs SQL implementacja

**Co poszło nie tak.** `InMemoryWorkflowRepository.get_by_task_execution_id` zwraca zawsze `None` (no-op stub), podczas gdy `SqlWorkflowRepository.get_by_task_execution_id` implementuje przez join po `task_execution.workflow_id`. Ten sam protokół, diametralnie różne zachowanie. Testy jednostkowe (in-memory) nigdy nie wyłapują regresji, która ujawnia się dopiero w SQL.

**Dlaczego to boli.** InMemory istnieje po to, by testować logikę domenową/aplikacyjną izolowane od bazy. Jeśli InMemory nie odzwierciedla semantyki SQL, testy jednostkowe dają fałszywe poczucie bezpieczeństwa.

**Prawidłowy wzorzec.** InMemory implementuje pełen kontrakt portu z identyczną semantyką co SQL. Jeśli metoda jest trudna w InMemory, to znaczy, że port ujawnia detal persystencji — wtedy napraw port, nie uproszczaj InMemory. Nigdy nie zostawiaj `return None` jako substytutu logiki.

---

## 7. Niepersistowane pola runtime (counters, waiting sets)

**Co poszło nie tak.** Agregat `GraphExecution` ma `parallel_groups`, `join_counters`, `loop_counters` modyfikowane przez metody domenowe. Ale model ORM nie ma tych kolumn, a mappery ich nie przepuszczają. Po reloadzie z bazy (restart procesu, inny worker) liczniki są puste → `get_or_create_loop_counter` tworzy nowy → **nieskończona pętla**, `join_counter` nigdy nie osiąga `wait_count`.

**Dlaczego to boli.** Pola, które uczestniczą w logice domenowej i ewoluują w czasie, muszą przetrwać restart procesu. Bez persystencji agregat budzi się z czystą kartą w połowie sagi.

**Prawidłowy wzorzec.** Każde pole agregatu, które jest modyfikowane po konstrukcji i wpływa na decyzje domenowe, musi być persystowane (kolumna lub JSON w modelu) i zmapowane w obu kierunkach. Reguła sprawdzania: round-trip test `entity → model → entity` zachowuje pole.

---

## 8. Martwy kod po zmianie typu zwrotnego

**Co poszło nie tak.** Refaktoryzacja zamieniła `get_by_task_execution_id(...) → GraphExecution | None` na `get_by_workflow_id(...) → list[GraphExecution]`. Handlery zostały zaktualizowane częściowo: po `if not graph_executions: return` i `graph_execution = graph_executions[0]` pozostał `if graph_execution is None: ...` — warunek **niedościgielny** (`list[0]` nigdy nie jest `None`).

**Dlaczego to boli.** Martwy kod sugeruje, że autor nie przemyślał nowej semantyki. Co gorsza, ukrywa to, że `list[0]` bez sortowania jest niedeterministyczne (patrz antywzorzec 9).

**Prawidłowy wzorzec.** Po zmianie typu zwrotnego metody (np. `X | None` → `list[X]`), przejrzyj wszystkich konsumentów i zaktualizuj logikę obsługi. Linter (ruff) wyłapuje martwe warunki typu `if x is None` po `x = non_optional`. Uruchamiaj go przed commitem.

---

## 9. Brak `order_by` na lookupach listowych

**Co poszło nie tak.** `get_by_workflow_id(...)` zwraca `list[GraphExecution]` bez `ORDER BY`. Handlery biorą `graph_executions[0]`. Kolejność zależy od bazy (SQL) lub kolejności wstawiania do dicta (in-memory) — niedeterministyczne przy przełączaniu backendów.

**Dlaczego to boli.** Kod który działa lokalnie (SQLite, mała baza) może wybrać inny graf na produkcji (Postgres, inny plan zapytania). Błąd niereprodukowalny.

**Prawidłowy wzorzec.** Każde zapytanie zwracające kolekcję, z której konsument bierze konkretny element (`[0]`, `first`), musi mieć jawny `order_by` (po `created_at`, `id`, lub innej kolumnie dającej stabilną kolejność). Jeśli jeden workflow powinien mieć dokładnie jeden GraphExecution — wymuś to invariantem (unique) zamiast zakładać `[0]`.

---

## 10. Nadpisywanie wyników domenowych przez różne ścieżki

**Co poszło nie tak.** `record_graph_node_execution_result` zapisuje wynik pod kluczem `graph_node_execution_id`. CrownScheduler woła ją dla noda, który **nigdy nie był faktycznie wykonany** (jest to join/planner w stanie `waiting`), z `stdout=str(combined_output)`. To **nadpisuje** oryginalny wynik Workera zapisany wcześniej pod tym samym kluczem, oraz emituje `CompletedEvent` dla noda, który fizycznie się nie wykonał.

**Dlaczego to boli.** Wynik "faktycznego wykonania noda" i "wake-up noda z `waiting` po ukończeniu dzieci" to semantycznie dwa różne wydarzenia. Traktowanie ich tą samą metodą gubi pierwotny wynik i myli konsumentów eventu.

**Prawidłowy wzorzec.** Rozdziel ścieżki: wynik faktycznego wykonania (`record_result`) vs. oznaczenie zakończenia oczekiwania (`on_children_completed`). Jeśli wspólna metoda, to z różnymi eventami i strażem przed nadpisaniem istniejącego wyniku.

---

## 11. Mutowalne referencje kolekcji z property

**Co poszło nie tak.** Properties `state_input`, `state_output`, `tags` zwracają bezpośrednią referencję do wewnętrznego dicta agregatu. Konsument wykonujący `graph.state_output["x"] = 1` zmienia wewnętrzny stan agregatu z pominięciem metod domenowych. Setter `state_output` też nie kopiuje — przypisuje referencję z zewnątrz.

**Dlaczego to boli.** Złamanie enkapsulacji: invariants agregatu mogą być naruszone z zewnątrz. Co gorsza, dwa agregaty mogą dzielić ten sam dict, jeśli jeden został przekazany do settera drugiego.

**Prawidłowy wzorzec.** Property zwracające kopię:

```python
@property
def state_output(self) -> dict[str, Any]:
    return dict(self._state_output)

@state_output.setter
def state_output(self, value: dict[str, Any]) -> None:
    self._state_output = dict(value)   # kopia na wejściu
```

Dla dictów zawierających mutowalne wartości (np. `dict[str, list[str]]`) — kopia głęboka na poziomie wartości: `{k: list(v) for k, v in self._items.items()}`.

---

## 12. Częściowy save bez atomowości

**Co poszło nie tak.** `CrownSchedulerHandler` robi `await uow.graph_executions.save(parent_graph)` (bez CAS), potem `await uow.workflow_repository.save(parent_workflow)` w `try/except WorkflowConcurrentlyModified`. Jeśli workflow.save rzuci wyjątek — graf już jest zmieniony i zapisany, ale workflow nie + eventy nie wystagedowane. Stan częściowy, niespójny.

**Dlaczego to boli.** Dwa zapisy w jednej operacji logicznej muszą być atomowe. Połowiczny commit zostawia system w stanie, którego nie da się automatycznie naprawić.

**Prawidłowy wzorzec.** Oba zapisy w jednej transakcji UoW (commit na `__aexit__` obejmujący oba repozytoria). Jeśli `WorkflowConcurrentlyModified` — retry całej sekcji (reload + ponowna mutacja + save obu), a nie tylko workflow. Ewentualnie CAS na obu repozytoriach, jeśli współbieżność jest realna.

---

## Krótka checklist antywzorcowa (przed commitem)

Przed wysłaniem zmian odpal tę listę w głowie:

- [ ] Każde nowe/usunięte pole agregatu dotknęło 6 miejsc (patrz antywzorzec 1)?
- [ ] Eventy przejścia stanu emitowane bezwarunkowo (antywzorzec 2)?
- [ ] Lookupy po unikalnym ID właściciela, nie współdzielonym FK (antywzorzec 3)?
- [ ] Model ORM ↔ migracja Alembic zgodne (antywzorzec 4)?
- [ ] Po usunięciu pola wszyscy konsumentowie mają nowe źródło (antywzorzec 5)?
- [ ] InMemory repo ma identyczną semantykę co SQL (antywzorzec 6)?
- [ ] Pola runtime są persystowane i mapowane obustronnie (antywzorzec 7)?
- [ ] Brak martwych warunków po zmianie typu zwrotnego (antywzorzec 8)?
- [ ] Kolekcje w zapytaniach mają `order_by` jeśli brany `[0]` (antywzorzec 9)?
- [ ] Wyniki wykonania vs. wake-up z `waiting` rozdzielone (antywzorzec 10)?
- [ ] Property zwracają kopie kolekcji (antywzorzec 11)?
- [ ] Zapisy w operacji logicznej atomowe (antywzorzec 12)?
