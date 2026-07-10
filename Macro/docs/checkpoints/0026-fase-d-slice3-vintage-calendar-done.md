# Macro Regime - Fase D - Slice 3: Vintage reale e calendario release FRED - Done

Data: 2026-07-10

## Scopo della fase

La Slice 3 completa la prima integrazione FRED/ALFRED introducendo due capacita' operative negli adapter Infrastructure:

- selezione del vintage reale piu' recente disponibile entro l'as-of date;
- client per calendario release FRED, globale e per singola release.

Il runtime core resta isolato dalla rete: Domain, Application e Web non chiamano HTTP. La rete resta in Infrastructure, composta dalla CLI solo quando si usa esplicitamente `--download-fred --fred-source http`.

## Riferimenti API ufficiali

- `fred/series/vintagedates`: `https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html`
- `fred/series/observations`: `https://fred.stlouisfed.org/docs/api/fred/series_observations.html`
- `fred/releases/dates`: `https://fred.stlouisfed.org/docs/api/fred/releases_dates.html`
- `fred/release/dates`: `https://fred.stlouisfed.org/docs/api/fred/release_dates.html`

## Cosa e' stato realizzato

### Catalogo baseline reale

Lo smoke reale ha evidenziato che i candidati PMI/ISM (`MANEMP_ISM`, poi `NAPM`) non sono `series_id` FRED validi. Poiche' FRED non espone un PMI/ISM utilizzabile nel catalogo ricercato, il baseline usa ora `INDPRO_YOY`, costruito scaricando la serie FRED `INDPRO` con trasformazione `units=pc1` (percent change from year ago).

Il normalizzatore `GROWTH_MOM` e' stato aggiornato di conseguenza: combina `INDPRO_YOY` e `SAHM`, invece del precedente placeholder `ISM_PMI` + `SAHM`.

Lo stesso smoke reale ha evidenziato che `BAMLH0A0HYM2` restituisce `HY_OAS` in percentuale, non in basis point. Il catalogo e il normalizzatore `CREDIT_STRESS` sono quindi stati riallineati alla scala FRED percentuale.

### Vintage reale nel downloader HTTP

`FredHttpMacroDataSource` ora, per ogni serie richiesta:

1. chiama `fred/series/vintagedates` con:
   - `series_id`;
   - `api_key`;
   - `file_type=json`;
   - `sort_order=desc`;
   - `limit=1`;
   - `realtime_end=asOf`;
2. seleziona il primo vintage date parsabile, cioe' il vintage reale piu' recente disponibile entro l'as-of;
3. chiama `fred/series/observations` con:
   - `series_id`;
   - `api_key`;
   - `file_type=json`;
   - `sort_order=desc`;
   - `limit=ObservationLimit`;
   - `observation_end=asOf`;
   - `vintage_dates=<vintage selezionato>`;
4. mappa la prima osservazione numerica utilizzabile in `FredObservation`.

Effetto pratico: `VintageDate` e `PublicationDate` nel file macro-data non sono piu' semplicemente l'as-of generico, ma riflettono il vintage reale restituito dalla risposta FRED/ALFRED.

### Calendario release

Nuovo adapter Infrastructure:

- `FredReleaseCalendarClient`
- `FredReleaseCalendarOptions`
- `FredReleaseDate`

Metodi:

- `FetchAllReleaseDatesAsync(...)`: chiama `fred/releases/dates`, utile per calendario globale.
- `FetchReleaseDatesAsync(...)`: chiama `fred/release/dates`, utile per calendario di una specifica release FRED.

Entrambi supportano:

- API key;
- base URI configurabile per test;
- `realtime_start` / `realtime_end`;
- `include_release_dates_with_no_data`;
- retry su `429`, `500`, `502`, `503`, `504`;
- parsing JSON senza dipendere dalla rete nei test.

## Test aggiunti/modificati

### `FredHttpMacroDataSourceTests`

- verifica che prima venga chiamato `series/vintagedates`;
- verifica che `series/observations` usi `vintage_dates=<vintage reale>`;
- verifica mapping di `PublicationDate` e `VintageDate` dal vintage restituito;
- verifica skip dei valori mancanti `"."`;
- verifica errore quando non ci sono vintage date;
- mantiene retry/error handling gia' introdotti in Slice 2.
- verifica fallback per serie disponibili in FRED ma non in ALFRED;
- verifica il parametro `units=pc1` per `INDPRO_YOY`.

### `FredReleaseCalendarClientTests`

- calendario globale `releases/dates`;
- calendario specifico `release/dates`;
- mapping `release_id`, `release_name`, `date`;
- `include_release_dates_with_no_data`;
- retry su errore transitorio;
- validazione API key.

## Verifiche eseguite

Mirata:

```text
dotnet test tests/MacroRegime.Infrastructure.Tests --no-restore --filter "FullyQualifiedName~FredHttpMacroDataSource|FullyQualifiedName~FredReleaseCalendarClient"
```

Esito iniziale: 10 test superati, 0 falliti.

Mirata finale:

```text
dotnet test tests\MacroRegime.Domain.Tests --no-restore --filter "FullyQualifiedName~FeatureNormalizer|FullyQualifiedName~BaselineRegimeDetector"
dotnet test tests\MacroRegime.Infrastructure.Tests --no-restore --filter "FullyQualifiedName~FredSeriesCatalog|FullyQualifiedName~FredHttpMacroDataSource|FullyQualifiedName~FredReleaseCalendarClient|FullyQualifiedName~FredStubMacroDataSource|FullyQualifiedName~JsonMacroDataFileWriter"
```

Esito finale mirato:

- Domain: 9 test superati, 0 falliti;
- Infrastructure: 27 test superati, 0 falliti.

Smoke reale:

```text
dotnet run --project src\MacroRegime.Cli --no-restore -- --download-fred --as-of 2026-07-01 --fred-source http --output-dir .tmp\smoke-fred-slice3
```

Esito: completato con 6 serie e 6 osservazioni. Il file prodotto contiene `INDPRO_YOY` da `INDPRO` con `Percent change` e `HY_OAS` con `Percent`.

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
- `MacroRegime.Application.Tests`: 27 test superati;
- `MacroRegime.Infrastructure.Tests`: 59 test superati;
- `MacroRegime.Reporting.Tests`: 2 test superati;
- `MacroRegime.Cli.Tests`: 12 test superati;
- `MacroRegime.Web.Tests`: 6 test superati;
- totale: 186 test superati, 0 falliti;
- nessun `HttpClient`/`System.Net.Http` nei sorgenti `.cs` di Domain/Application/Web;
- `HttpClient` presente solo in `src/MacroRegime.Infrastructure/External/FredHttpMacroDataSource.cs` e `src/MacroRegime.Infrastructure/External/FredReleaseCalendarClient.cs`.

## Gate architetturali

- `HttpClient` resta confinato in `MacroRegime.Infrastructure`.
- `MacroRegime.Domain`: nessuna rete.
- `MacroRegime.Application`: nessuna rete; le porte restano astratte.
- `MacroRegime.Web`: nessuna rete e nessun downloader.
- `MacroRegime.Cli`: unico punto di composizione operativa del downloader.

## Cosa resta fuori

- Uso UI del calendario release.
- Persistenza dedicata del calendario release.
- Backoff avanzato e rate-limit stateful.
- Provider market data esterni.
- Dataset storico ampio gia' popolato.

## Valutazione

Fase D - Slice 3 completata a livello adapter: il download HTTP usa un vintage reale selezionato via API FRED/ALFRED e Infrastructure dispone di un client calendario release testato. Il runtime core conserva l'isolamento di rete stabilito da ADR 0004.
