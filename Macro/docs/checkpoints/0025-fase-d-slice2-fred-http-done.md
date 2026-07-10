# Macro Regime - Fase D - Slice 2: Client HTTP FRED reale - Done

Data: 2026-07-10

## Scopo della fase

La Slice 2 della Fase D introduce un client HTTP reale verso FRED, mantenendo l'isolamento deciso in ADR 0004: la rete resta confinata in `MacroRegime.Infrastructure` e viene composta solo dalla CLI nel modo esplicito `--download-fred`.

La Slice 3 resta fuori scope: vintage ALFRED multi-vintage, calendario rilasci reale e logica point-in-time avanzata.

## Cosa e' stato realizzato

### Infrastructure - nuovo adapter HTTP

- `FredHttpMacroDataSource`: implementa `IExternalMacroDataSource` usando `HttpClient`.
- `FredHttpMacroDataSourceOptions`: configura API key, base URI, numero tentativi, ritardo retry e limite osservazioni.
- Endpoint FRED usato: `fred/series/observations`, `file_type=json`.
- Parametri usati per serie:
  - `series_id` dal `FredSeriesCatalog`;
  - `api_key`;
  - `observation_end = asOf`;
  - `realtime_start = asOf`;
  - `realtime_end = asOf`;
  - `sort_order = desc`;
  - `limit = 30`.
- Parsing: prende la prima osservazione utilizzabile, ignorando valori FRED mancanti `"."`.
- Error handling:
  - `InvalidDataException` se la risposta e' vuota, non contiene osservazioni utilizzabili o restituisce errore HTTP finale;
  - retry su `429`, `500`, `502`, `503`, `504`;
  - `ArgumentException` se API key o opzioni non sono valide.

Riferimenti API ufficiali consultati:

- `https://fred.stlouisfed.org/docs/api/fred/series_observations.html`
- `https://fred.stlouisfed.org/docs/api/api_key.html`

### CLI - selezione sorgente FRED

- `--download-fred` resta il comando esplicito per produrre `macro-data-{asOf}.json`.
- Nuova opzione `--fred-source stub|http`.
  - Default: `stub`, per mantenere il comportamento deterministico della Slice 1.
  - `http`: usa `FredHttpMacroDataSource`.
- Nuova opzione `--fred-api-key`.
  - Fallback: variabile ambiente `FRED_API_KEY`.
  - Se `--fred-source http` non trova una API key, la CLI ritorna usage error (`1`) senza scrivere output.
- La pipeline di analisi resta separata: il download scrive solo il file macro-data, senza run/report.

### Writer

- `JsonMacroDataFileWriter` usa ora `source: "FRED"` invece di `FRED-Stub`, per rappresentare sia dati stub sia dati HTTP reali senza cambiare il contratto Application.

## Test aggiunti

### Infrastructure

`FredHttpMacroDataSourceTests` copre:

- costruzione della richiesta HTTP con endpoint e parametri corretti;
- mapping FRED -> `FredObservation`;
- salto dei valori mancanti `"."`;
- errore quando non esistono osservazioni utilizzabili;
- retry su stato transitorio (`429`);
- validazione API key obbligatoria.

I test usano un `HttpMessageHandler` fake, quindi non accedono a Internet e non richiedono una API key reale.

### CLI

`MacroRegimeCliTests` esteso con:

- errore di usage quando `--fred-source http` non ha `--fred-api-key` ne' `FRED_API_KEY`;
- errore di usage per sorgente sconosciuta.

## Verifiche eseguite

Comandi mirati:

```text
dotnet test tests/MacroRegime.Infrastructure.Tests --no-restore --filter FredHttpMacroDataSource
dotnet test tests/MacroRegime.Cli.Tests --no-restore --filter DownloadFred
```

Esito:

- `FredHttpMacroDataSourceTests`: 5 test superati;
- `DownloadFred` CLI tests: 5 test superati.

Verifica finale:

```text
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore
rg -n "HttpClient|System\.Net\.Http" src\MacroRegime.Domain src\MacroRegime.Application src\MacroRegime.Web -g "*.cs" -g "!**/bin/**" -g "!**/obj/**"
rg -n "HttpClient|System\.Net\.Http" src\MacroRegime.Infrastructure -g "*.cs" -g "!**/bin/**" -g "!**/obj/**"
```

Esito finale:

- build superata, 0 warning, 0 errori;
- `MacroRegime.Domain.Tests`: 79 test superati;
- `MacroRegime.Application.Tests`: 27 test superati;
- `MacroRegime.Infrastructure.Tests`: 53 test superati (+5 nuovi Slice 2);
- `MacroRegime.Reporting.Tests`: 2 test superati;
- `MacroRegime.Cli.Tests`: 12 test superati (+2 nuovi Slice 2);
- `MacroRegime.Web.Tests`: 6 test superati;
- totale: 179 test superati, 0 falliti;
- nessun `HttpClient`/`System.Net.Http` nei sorgenti `.cs` di Domain/Application/Web;
- `HttpClient` presente solo in `src/MacroRegime.Infrastructure/External/FredHttpMacroDataSource.cs`.

## Gate architetturali

- `HttpClient` e' introdotto solo in `MacroRegime.Infrastructure`.
- `MacroRegime.Domain`: nessuna rete.
- `MacroRegime.Application`: nessuna rete; resta solo la porta `IExternalMacroDataSource`.
- `MacroRegime.Web`: nessuna rete e nessun downloader.
- `MacroRegime.Cli`: unico punto di composizione del downloader.

## Cosa resta fuori

- Vintage ALFRED multi-vintage e gestione avanzata point-in-time.
- Calendario rilasci FRED reale.
- Gestione rate-limit persistente o backoff sofisticato.
- Provider market data esterni.
- UI Web per il download.

## Valutazione

Fase D - Slice 2 completata a livello implementativo: il sistema puo' produrre file macro-data da FRED reale tramite CLI, ma mantiene lo stub come default e conserva l'isolamento del runtime core.
