# Macro Regime - Fase D - Slice 5: Dataset storico macro+market - Done

Data: 2026-07-10

## Scopo della fase

La Slice 5 chiude la Fase D trasformando gli adapter esterni macro e market data in un artefatto utilizzabile dalla Fase E: un dataset storico file-based che combina input as-of e forward returns.

## Cosa e' stato realizzato

### Builder dataset

Nuovo componente Infrastructure:

- `HistoricalDatasetBuilder`

Input:

- directory con `macro-data-yyyy-MM-dd.json`;
- directory con `market-data-yyyy-MM-dd.json`;
- intervallo `from/to`;
- orizzonti forward return in giorni.

Output:

- `historical-dataset-{from}-{to}.json`

Record JSON:

- `HistoricalDatasetRecord`
- `HistoricalDatasetRowRecord`
- `HistoricalForwardReturnRecord`

Ogni riga contiene:

- `asOfDate`;
- osservazioni macro disponibili as-of;
- osservazioni market disponibili as-of;
- forward returns per simbolo e orizzonte.

### Forward returns

Per ogni as-of date e orizzonte:

1. usa i prezzi market osservati all'as-of come start value;
2. cerca la prima data market disponibile uguale o successiva a `asOf + horizonDays`;
3. calcola `(future / start) - 1`;
4. salta simboli con start value zero o valore futuro mancante.

Questa scelta evita di richiedere file esatti su weekend/festivi e resta coerente con un dataset giornaliero file-based.

### CLI

Nuovo comando:

```text
--build-historical-dataset --dataset-from yyyy-MM-dd --dataset-to yyyy-MM-dd --macro-data-dir path --market-data-dir path [--forward-return-days 28,56,91] [--output-dir path]
```

Il comando e' separato dai downloader e dalla pipeline di analisi: legge solo file locali e produce un artefatto di ricerca.

## Fuori scope

- Popolare automaticamente anni di dati reali.
- Calcolare metriche Fase E come asset alignment, tilt simulation o walk-forward.
- Ottimizzare storage/query su dataset grandi.
- UI per esplorazione dataset.

Questi punti appartengono alla Fase E o a una successiva fase di data operations.

## Verifiche eseguite

Mirate:

```text
dotnet test tests\MacroRegime.Infrastructure.Tests --no-restore --filter FullyQualifiedName~HistoricalDatasetBuilder
dotnet test tests\MacroRegime.Cli.Tests --no-restore --filter FullyQualifiedName~BuildHistoricalDataset
```

Esito:

- Infrastructure: 3 test superati;
- CLI: 2 test superati.

Smoke locale end-to-end:

```text
dotnet run --project src\MacroRegime.Cli --no-restore -- --download-fred --as-of 2026-07-01 --output-dir .tmp\smoke-dataset-slice5\macro
dotnet run --project src\MacroRegime.Cli --no-restore -- --download-market-data --as-of 2026-07-01 --output-dir .tmp\smoke-dataset-slice5\market
dotnet run --project src\MacroRegime.Cli --no-restore -- --download-market-data --as-of 2026-07-29 --output-dir .tmp\smoke-dataset-slice5\market
dotnet run --project src\MacroRegime.Cli --no-restore -- --build-historical-dataset --dataset-from 2026-07-01 --dataset-to 2026-07-01 --macro-data-dir .tmp\smoke-dataset-slice5\macro --market-data-dir .tmp\smoke-dataset-slice5\market --forward-return-days 28 --output-dir .tmp\smoke-dataset-slice5\dataset
```

Esito:

- macro snapshot: 6 osservazioni;
- market snapshot as-of: 6 osservazioni;
- market snapshot futuro: 6 osservazioni;
- dataset storico: 1 riga, 6 forward returns.

Verifica finale:

```text
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore
rg -n "HttpClient|System\.Net\.Http" src\MacroRegime.Domain src\MacroRegime.Application src\MacroRegime.Web -g "*.cs" -g "!**/bin/**" -g "!**/obj/**"
rg -n "HttpClient|System\.Net\.Http" src\MacroRegime.Infrastructure -g "*.cs" -g "!**/bin/**" -g "!**/obj/**"
```

Esito finale:

- build superata, 0 warning, 0 errori;
- `MacroRegime.Domain.Tests`: 80 test superati;
- `MacroRegime.Application.Tests`: 30 test superati;
- `MacroRegime.Infrastructure.Tests`: 76 test superati;
- `MacroRegime.Reporting.Tests`: 2 test superati;
- `MacroRegime.Cli.Tests`: 17 test superati;
- `MacroRegime.Web.Tests`: 6 test superati;
- totale: 211 test superati, 0 falliti;
- nessun `HttpClient`/`System.Net.Http` nei sorgenti `.cs` di Domain/Application/Web;
- `HttpClient` presente solo in adapter Infrastructure.

## Valutazione

Fase D completa: il progetto dispone di adapter esterni macro e market data, download offline in CLI, output JSON locali leggibili dal runtime e un dataset storico macro+market con forward returns. La Fase E puo' partire usando questi artefatti senza introdurre rete nel runtime core.
