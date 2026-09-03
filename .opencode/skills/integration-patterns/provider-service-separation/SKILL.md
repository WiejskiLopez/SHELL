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

- `GraphDefinitionProviderHttpAdapter`;
- `SessionQueryProviderHttpAdapter`;
- `UserIdentityProviderHttpAdapter`.

Port providera należy do BC, który potrzebuje danych. Jego typy wejściowe i wyjściowe należą do konsumującego BC albo do platformowych kontraktów technicznych. Zwracaj tylko minimalny lokalny VO, snapshot albo read model wymagany przez konsumenta.

```text
execution domain port:
    GraphDefinitionProvider
        -> GraphDefinition

execution infrastructure:
    GraphDefinitionProviderHttpAdapter
        HTTP response -> local contract V1 -> local mapper -> GraphDefinition
```

Provider zwraca minimalny lokalny VO, snapshot albo read model wymagany przez konsumenta;
dane źródła są mapowane (HTTP → lokalny kontrakt → lokalny VO), a mutacje pozostają po stronie
źródłowego BC. Zakres providera obejmuje:

- dane używane przez lokalną domenę (bez zbędnych pól);
- model mapowany z transportu (surowe `dict`, JSON ani ORM do domeny);
- wyłącznie odczyt.

## Service/Command Port: operacja lub mutacja

Port operacji (`Command Port`) służy do zlecenia operacji w innym BC albo do wywołania jego zachowania. Zgodnie z wzorcem `aggregate-command-port`, port nazywamy `<Czasownik><Obiekt>Port`; nazwa wskazuje działanie, nie odczyt.

Przykłady nazw:

- `WorkflowSessionCommandPort`;
- `PaymentAuthorizationPort`;
- `TaskExecutionTriggerPort`.

Port serwisu należy do BC zlecającego operację. Zwraca wyłącznie lokalny wynik operacji, identyfikator, status albo wynik wykonania zdefiniowany przez konsumenta. Nie zwraca obcego agregatu.

```text
session domain/application port:
    WorkflowSessionCommandPort
        add_session_output(...) -> None

session infrastructure:
    WorkflowSessionCommandHttpAdapter
        local command -> versioned HTTP request -> remote operation result
```

Port operacji realizuje operacje na zasobie w innym BC; zwykły odczyt pokrywa Provider/QueryService,
a zmiana dwóch agregatów bez jawnej orkiestracji (proces/saga) pozostaje poza wzorcem portu.
Zakres portu operacji obejmuje:

- utworzenie, zmianę albo usunięcie zasobu w innym BC (lub uruchomienie komendy/procesu);
- rozpoczęcie operacji asynchronicznej i zwrot operation ID;
- mapowanie błędu transportowego na lokalny błąd portu.
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
- `Command Port` może używać HTTP dla szybkiej komendy albo eventu/command busa dla operacji długiej, odpornej na chwilową niedostępność i eventual consistency.
- Długotrwałe operacje wielo-BC należą do `process/` i są koordynowane przez sagę/process manager, nie przez pojedynczy provider.

## Checklist

Przed dodaniem integracji odpowiedz:

1. Czy tylko czytam dane? Użyj `Provider`.
2. Czy żądam wykonania, utworzenia, zmiany, usunięcia lub uruchomienia procesu? Użyj Command Port (`<Czasownik><Obiekt>Port`).
3. Który BC potrzebuje tej funkcji? On jest właścicielem portu.
4. Jakie minimalne lokalne VO/read model/result są potrzebne?
5. Czy adapter waliduje wersjonowany transport i mapuje go lokalnie?
6. Czy przekazuję wyłącznie ID-y zamiast zagnieżdżonych obcych agregatów?
7. Czy operacja wielo-BC wymaga sagi zamiast ukrytej mutacji w adapterze?
8. Czy kontrakt ma test w `shell/tests/contracts/`?
