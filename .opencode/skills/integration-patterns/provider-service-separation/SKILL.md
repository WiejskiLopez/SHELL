---
name: provider-service-separation
description: Zasady rozdzielenia providerów od serwisów w komunikacji między bounded contextami. Używaj przy projektowaniu portów i adapterów do odczytu danych z innego BC oraz przy operacjach, które modyfikują lub wykonują akcję w innym BC.
---

# Provider i Service w integracji BC

## Cel

Każdy bounded context zachowuje własność swoich agregatów i modeli domenowych. BC konsumujący definiuje minimalny port odpowiadający jego potrzebie, a infrastruktura dostarcza implementację lokalną, HTTP, gRPC albo eventową.

Nie przenoś do konsumującego BC agregatu, encji, DTO aplikacyjnego, response modelu ani modelu ORM z BC źródłowego.

## Provider: tylko odczyt

`Provider` służy do pobierania danych potrzebnych do podjęcia decyzji lub wykonania lokalnej operacji. Nie tworzy, aktualizuje ani usuwa zasobów w źródłowym BC.

Przykłady nazw:

- `GraphExecutionDefinitionProvider`;
- `SessionQueryProvider`;
- `UserIdentityProvider`.

Port providera należy do BC, który potrzebuje danych. Jego typy wejściowe i wyjściowe należą do konsumującego BC albo do platformowych kontraktów technicznych. Zwracaj tylko minimalny lokalny VO, snapshot albo read model wymagany przez konsumenta.

```text
execution domain port:
    GraphExecutionDefinitionProvider
        -> GraphExecutionDefinition

execution infrastructure:
    GraphExecutionDefinitionHttpProvider
        HTTP response -> local contract V1 -> local mapper -> GraphExecutionDefinition
```

Provider nie powinien:

- zwracać `GraphDefinitionResponse` z BC `definition`;
- zwracać agregatu `GraphDefinition` albo `NodeDefinition` ze źródłowego BC;
- przekazywać surowego `dict`, JSON albo modelu ORM do domeny;
- pobierać pól, których lokalna domena nie używa;
- wykonywać mutacji po stronie źródłowego BC.

## Service: operacja lub mutacja

`Service` służy do zlecenia operacji w innym BC albo do wywołania jego zachowania. Nazwa wskazuje działanie, nie odczyt.

Przykłady nazw:

- `WorkflowSessionCommandService`;
- `PaymentAuthorizationService`;
- `TaskExecutionTriggerService`.

Port serwisu należy do BC zlecającego operację. Zwraca wyłącznie lokalny wynik operacji, identyfikator, status albo wynik wykonania zdefiniowany przez konsumenta. Nie zwraca obcego agregatu.

```text
session domain/application port:
    WorkflowSessionCommandService
        add_session_output(...) -> None

session infrastructure:
    WorkflowSessionHttpService
        local command -> versioned HTTP request -> remote operation result
```

Service może:

- utworzyć, zmienić albo usunąć zasób w innym BC;
- uruchomić proces lub komendę w innym BC;
- rozpocząć operację asynchroniczną i zwrócić operation ID;
- mapować błąd transportowy na lokalny błąd portu.

Service nie powinien:

- być używany do zwykłego odczytu query;
- udawać lokalnego repozytorium obcego BC;
- zmieniać dwóch agregatów bez jawnej orkiestracji procesu lub sagi;
- przenosić transakcji lokalnego BC do zewnętrznego BC.

## Kontrakt transportowy i mapowanie

Właścicielem publicznego response/request jest BC, który wystawia endpoint. Konsument nie importuje tych klas. Adapter posiada lokalny, wersjonowany model kontraktu tylko dla pól, których potrzebuje:

```text
remote API V1 response
    -> consumer-local ResponseV1
    -> mapper / Anti-Corruption Layer
    -> consumer VO, snapshot albo result
```

Dodatkowe pola odpowiedzi są ignorowane. Brak wymaganych pól jest błędem kontraktu, a nie powodem do ustawiania fałszywych wartości domyślnych.

Dla endpointów złożonych z wielu agregatów nazwij response read modelem, np. `GraphDefinitionTopologyResponseV1`, a nie response agregatu. Agregatowy response zwraca wyłącznie stan właściciela agregatu. Projekcja z wielu agregatów musi być jawnie nazwana i mieć osobny przypadek użycia.

## Lokalizacja

Lokalizację portów (katalog `ports/` — odczyt i operacje razem) oraz adapterów
opisują wzorce Aggregate Provider i Command Port. Nie umieszczaj portu w BC źródłowym.

## Synchronicznie czy asynchronicznie

- `Provider` zwykle używa synchronicznego HTTP query, gdy dane są potrzebne natychmiast.
- `Service` może używać HTTP dla szybkiej komendy albo eventu/command busa dla operacji długiej, odpornej na chwilową niedostępność i eventual consistency.
- Długotrwałe operacje wielo-BC należą do `process/` i są koordynowane przez sagę/process manager, nie przez pojedynczy provider.

## Checklist

Przed dodaniem integracji odpowiedz:

1. Czy tylko czytam dane? Użyj `Provider`.
2. Czy żądam wykonania, utworzenia, zmiany, usunięcia lub uruchomienia procesu? Użyj `Service`.
3. Który BC potrzebuje tej funkcji? On jest właścicielem portu.
4. Jakie minimalne lokalne VO/read model/result są potrzebne?
5. Czy adapter waliduje wersjonowany transport i mapuje go lokalnie?
6. Czy przekazuję wyłącznie ID-y zamiast zagnieżdżonych obcych agregatów?
7. Czy operacja wielo-BC wymaga sagi zamiast ukrytej mutacji w adapterze?
8. Czy kontrakt ma test w `shell/tests/contracts/`?
