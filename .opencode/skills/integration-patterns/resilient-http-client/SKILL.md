---
name: resilient-http-client
description: "Zasady uzywania ResilientAsyncClient w komunikacji HTTP miedzy mikroserwisami SHELL. Uzywaj przy projektowaniu, implementacji i review adapterow HTTP, polityk retry, timeoutow, circuit breakera oraz konfiguracji klientow w DI."
---

# Resilient HTTP Client

## Cel

`ResilientAsyncClient` jest wspolnym technicznym mechanizmem platformy dla
wychodzacych wywolan HTTP. Ogranicza czas oczekiwania, liczbe ponowien i wplyw
awarii zaleznosci na mikroserwis wywolujacy.

Nie jest klientem biznesowym i nie zna bounded contextow, DTO, agregatow ani
fallbackow domenowych.

## Gdzie uzywac

Uzywaj klienta w adapterze HTTP konkretnego mikroserwisu, gdy ten mikroserwis
wywoluje inny serwis albo zewnetrzna zaleznosc przez HTTP.

- klient i retry sa generycznym mechanizmem `shell.platform`;
- adapter nalezy do mikroserwisu konsumujacego;
- konfiguracja klienta nalezy do jego `bootstrap` i srodowiska wdrozeniowego;
- port domenowy lub aplikacyjny nie moze zalezec od `httpx` ani klienta platformy;
- klient przyjmuje jawny `base_url`, timeout, klucz uslugi i polityki odpornosci.

Nie uzywaj klienta do:

- obslugi przychodzacych endpointow FastAPI;
- komunikacji przez RabbitMQ, inbox lub outbox;
- dostepu do bazy danych;
- zastapienia publicznego kontraktu HTTP adapterem znajacym cudze modele;
- wywolania, ktore powinno byc asynchronicznym eventem.

## Skladanie w DI

Klient tworzy sie w composition root konkretnego mikroserwisu. Nie tworz klienta
w handlerze, agregacie ani module domenowym.

```python
ResilientAsyncClient(
    base_url=dependency_url,
    service_api_key=dependency_api_key,
    timeout=timeout,
    retry_policy=RetryPolicy(max_attempts=3),
    circuit_breaker_policy=CircuitBreakerPolicy(
        failure_threshold=5,
        recovery_timeout=15.0,
    ),
)
```

Kazda zaleznosc otrzymuje osobny klient albo osobny obwod. Awaria Definition
nie moze otwierac obwodu dla Session. Nie uzywaj jednego globalnego singletona
dla wszystkich zaleznosci i mikroserwisow.

## Retry

Retry musi byc jawne, ograniczone i zgodne z semantyka operacji.

Domyslna polityka:

- ponawiaj przede wszystkim `GET`;
- ponawiaj bledy transportowe oraz `429`, `502`, `503`, `504`;
- stosuj exponential backoff, jitter i maksymalny delay;
- uwzgledniaj `Retry-After`, jezeli kontrakt i implementacja to obsluguja;
- po ostatniej probie zwroc odpowiedz albo podnies typowany blad transportowy.

Nie ponawiaj automatycznie:

- `POST`, `PUT`, `PATCH`, `DELETE`, jezeli idempotencja nie jest potwierdzona;
- `401`, `403` i bledow walidacji;
- bledow mapowania kontraktu;
- operacji, ktorych ponowne wykonanie moze zmienic stan.

Komenda moze miec retry tylko z jawnym `idempotency_key` i kontraktem odbiorcy.
Sam circuit breaker ani timeout nie zapewniaja idempotencji.

## Timeout

Kazde wywolanie musi miec skonfigurowany skonczony timeout. Preferuj osobne
limity connect, read, write i pool, gdy wymagaja tego zaleznosci.

Timeout nie moze byc nieskonczony ani ukryty w domyslnym kliencie. Wartosci
ustawia sie per zaleznosc, a ich limity waliduje podczas startu.

## Circuit breaker

Circuit breaker jest izolowany per klient i zaleznosc:

```text
CLOSED -> OPEN -> HALF_OPEN -> CLOSED
```

- `CLOSED`: wywolania sa przepuszczane;
- `OPEN`: wywolania sa odrzucane lokalnie po przekroczeniu progu bledow;
- `HALF_OPEN`: przepuszczana jest ograniczona proba powrotu;
- sukces zamyka obwod, porazka otwiera go ponownie.

Otwarcie obwodu musi byc mierzalne i mapowane na jawny blad zaleznosci. Nie
zwracaj cicho pustych danych dla wymaganej zaleznosci.

## Uwierzytelnienie i korelacja

Klient powinien przekazywac:

- `X-API-Key` albo docelowo token workload identity/mTLS;
- `X-Correlation-ID` z aktualnego kontekstu;
- `causation_id`, gdy wymaga tego kontrakt integracyjny.

Sekretow nie wolno zapisywac w logach, wyjatkach, URL-ach ani payloadach.
Klucze uslugi musza pochodzic z konfiguracji wdrozeniowej lub secret managera.

`X-API-Key` jest mechanizmem przejsciowym. Docelowo preferowane sa mTLS,
service mesh albo krotkotrwale tokeny workload identity.

## Graceful degradation

`ResilientAsyncClient` nie implementuje fallbackow biznesowych. Fallback nalezy
do adaptera, application albo process konkretnego mikroserwisu.

Dopuszczalne zachowania musza byc jawne:

- opcjonalny odczyt zwraca pusty wynik;
- cache zwraca ostatnia poprawna projekcje;
- proces odklada prace do kolejki;
- operacja krytyczna zwraca kontrolowany blad zaleznosci.

Nie ukrywaj niedostepnosci wymaganej uslugi przez fikcyjny sukces.

## Testy wymagane przy uzyciu klienta

Adapter powinien miec testy z `httpx.MockTransport` obejmujace:

- timeout i blad transportowy;
- pojedynczy `503`, po ktorym nastepuje sukces;
- trwale bledy i przejscie obwodu do `OPEN`;
- odrzucenie wywolania przez otwarty obwod bez ruchu sieciowego;
- powrot zaleznosci i przejscie `HALF_OPEN -> CLOSED`;
- brak retry dla metod nieidempotentnych;
- brak retry dla `401`, `403` i bledow walidacji;
- propagacje correlation ID i klucza uslugi;
- brak sekretu w logach i wyjatkach;
- jawny fallback albo jawny blad, zalezne od kontraktu.

Testy musza kontrolowac zegar, sleep i losowosc backoffu, aby byly
powtarzalne. Nie uzywaj prawdziwej sieci w testach jednostkowych.

## Checklist review

- [ ] Czy jest to rzeczywiste wychodzace wywolanie HTTP?
- [ ] Czy adapter nalezy do mikroserwisu konsumujacego?
- [ ] Czy klient jest skladany w `bootstrap`/DI?
- [ ] Czy timeout jest skonczony i namespaced per zaleznosc?
- [ ] Czy retry obejmuje tylko operacje bezpieczne lub idempotentne?
- [ ] Czy retry ma limit prob, backoff i jitter?
- [ ] Czy obwod jest izolowany per zaleznosc?
- [ ] Czy bledy sa jawne i obserwowalne?
- [ ] Czy sekrety nie trafiaja do logow ani URL-i?
- [ ] Czy sa testy awarii bez prawdziwej sieci?
- [ ] Czy fallback nalezy do warstwy znajacej znaczenie biznesowe?
- [ ] Czy zmiana nie dodaje zaleznosci BC do `platform`?

## Aktualny stan SHELL

W SHELL `Execution` jest pierwszym pilotem. `Definition` i `Session` sa
obslugiwane przez `ResilientAsyncClient` skladany w `ExecutionCoreContainer`.
Pozostale mikroserwisy nie powinny dostac klienta automatycznie, dopoki nie maja
rzeczywistych wychodzacych adapterow HTTP.
