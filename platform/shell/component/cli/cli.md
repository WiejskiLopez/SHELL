# Moduł `cli`

Odpowiada za parsowanie argumentów wiersza poleceń i udostępnianie ich reszcie aplikacji.

## Odpowiedzialność

- Parsuje `sys.argv` i zapisuje wartości do `CliProperties`.
- Waliduje wymagane parametry — błędy zgłaszane asercjami.
- Jedynym dozwolonym sposobem odczytu parametrów CLI przez inne moduły jest właściwość `cli_properties_`.

## Submoduły

- `cli/` — klasa `Cli`: węzeł DOM przechowujący sparsowane argumenty i aktualizujący placeholdery.
- `cli_properties/` — klasa `CliProperties`: interfejs do parametrów CLI z walidacją i wartościami domyślnymi.
