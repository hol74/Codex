# Macro Regime - Fase D - Slice 4: Provider market data esterno - Done

Data: 2026-07-10

## Scopo della fase

La Slice 4 rende esplicito il provider esterno per dati di mercato, necessario prima della Fase E per valutare l'efficacia delle probabilita' di regime rispetto agli andamenti successivi degli asset.

La rete resta confinata in `MacroRegime.Infrastructure` e viene composta solo dalla CLI in modalita' offline.

## Valutazione provider Yahoo

Yahoo Finance e' stato valutato come provider pragmatico per uso personale/ricerca:

- copre ETF liquidi e indici ampi utili come proxy di asset class;
- non richiede API key per lo smoke operativo del chart endpoint usato;
- permette di scaricare adjusted close giornalieri;
- non va pero' trattato come API ufficiale garantita: la documentazione yfinance segnala che non e' affiliata, approvata o verificata da Yahoo e che l'uso dei dati va verificato rispetto ai termini Yahoo.

Decisione: usare Yahoo solo come adapter sostituibile `YahooMarketDataSource`, non come contratto di dominio. Lo stub resta default.

## Cosa e' stato realizzato

### Application

Nuovi tipi:

- `MarketDataObservation`
- `MarketDataSeriesSet`
- `MarketDataFetchCommand`
- `DownloadMarketDataCommand`
- `DownloadMarketDataResult`
- `DownloadMarketDataUseCase`

Nuove porte:

- `IExternalMarketDataSource`
- `IMarketDataFileWriter`

### Infrastructure

Nuovi adapter:

- `MarketDataSeriesCatalog`
- `MarketDataStubDataSource`
- `JsonMarketDataFileWriter`
- `YahooMarketDataSource`

Baseline market data:

- `SPY`: US equity proxy;
- `ACWI`: global equity proxy;
- `IEF`: government bond proxy;
- `GLD`: gold proxy;
- `BIL`: cash proxy;
- `HYG`: high-yield credit proxy.

Il writer produce `market-data-{asOf:yyyy-MM-dd}.json` nello schema snapshot v1 esistente, con:

- `macroObservations: []`;
- `marketObservations` popolato;
- file leggibile da `JsonDataSnapshotProvider`.

### CLI

Nuovo comando offline:

```text
--download-market-data --as-of yyyy-MM-dd [--market-source stub|yahoo] [--output-dir path]
```

`--market-source stub` resta il default deterministico. `--market-source yahoo` usa `YahooMarketDataSource`.

## Fuori scope intenzionale

- Merge automatico macro+market in un unico dataset storico.
- Forward returns 4/8/13 settimane.
- Metriche di valutazione asset alignment.
- Persistenza dedicata market data.
- UI per ispezione market data.

Il merge macro+market e i forward returns sono stati completati nello step successivo, tracciato nel checkpoint `0028-fase-d-complete-dataset-storico-done.md`. Restano fuori da Slice 4, ma non dalla Fase D complessiva.

## Verifiche eseguite

Mirate:

```text
dotnet test tests\MacroRegime.Application.Tests --no-restore --filter FullyQualifiedName~DownloadMarketDataUseCase
dotnet test tests\MacroRegime.Infrastructure.Tests --no-restore --filter "FullyQualifiedName~MarketDataSeriesCatalog|FullyQualifiedName~MarketDataStubDataSource|FullyQualifiedName~JsonMarketDataFileWriter|FullyQualifiedName~YahooMarketDataSource"
dotnet test tests\MacroRegime.Cli.Tests --no-restore --filter FullyQualifiedName~DownloadMarketData
```

Esito:

- Application: 3 test superati;
- Infrastructure: 14 test superati;
- CLI: 3 test superati.

Smoke locali/reali:

```text
dotnet run --project src\MacroRegime.Cli --no-restore -- --download-market-data --as-of 2026-07-01 --output-dir .tmp\smoke-market-slice4-stub
dotnet run --project src\MacroRegime.Cli --no-restore -- --download-market-data --as-of 2026-07-01 --market-source yahoo --output-dir .tmp\smoke-market-slice4-yahoo
```

Esito:

- stub: 6 serie e 6 osservazioni;
- Yahoo: 6 serie e 6 osservazioni;
- il file Yahoo contiene `macroObservations: []` e 6 `marketObservations` con adjusted close.

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
- `MacroRegime.Infrastructure.Tests`: 73 test superati;
- `MacroRegime.Reporting.Tests`: 2 test superati;
- `MacroRegime.Cli.Tests`: 15 test superati;
- `MacroRegime.Web.Tests`: 6 test superati;
- totale: 206 test superati, 0 falliti;
- nessun `HttpClient`/`System.Net.Http` nei sorgenti `.cs` di Domain/Application/Web;
- `HttpClient` presente solo in adapter Infrastructure.

## Valutazione

Slice 4 completata a livello adapter: il sistema ora puo' produrre dati di mercato esterni in file JSON locali, senza introdurre rete nel runtime core. Questo sblocca il prossimo passo naturale: costruire un dataset storico macro+market e calcolare forward returns per validare le probabilita' dei regimi.
