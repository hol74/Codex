# Macro Regime - Fase D - Slice 1: Adapter FRED isolato con stub - Done

Data: 2026-07-10

## Scopo della fase

La Fase D del piano operativo (`docs/0001-piano-operativo.md`) introduce i provider dati esterni FRED/ALFRED dietro le porte applicative esistenti, con vintage reale e calendario rilasci, e con il vincolo non negoziabile che il runtime core non abbia dipendenze di rete.

Questa e' la Slice 1: architettura dell'adapter isolato + stub deterministico, senza HTTP reale. HTTP reale, vintage ALFRED e calendario rilasci sono rimandati alle Slice 2 e 3.

## Cosa e' stato realizzato

### Application - nuovi tipi e porta

- `FredObservation`: record FRED-style con `SeriesId`, `SeriesCode`, `ObservationDate`, `PublicationDate`, `VintageDate`, `Value`, `Unit`.
- `FredSeriesSet`: set di serie richieste, con `Baseline` (6 serie allineate ai sample esistenti).
- `FredFetchCommand`: command per la porta.
- `DownloadMacroDataCommand` / `DownloadMacroDataResult`: command e result del use case.
- `DownloadMacroDataUseCase`: orchestratore fetch -> scrivi file.
- `IExternalMacroDataSource`: porta applicativa per il download.
- `IMacroDataFileWriter`: porta applicativa per la scrittura del file macro-data.

### Infrastructure - nuovi adapter

- `FredSeriesCatalog`: catalogo baseline di 6 serie (`ISM_PMI`, `SAHM`, `T10YIE`, `VIX`, `YC_10Y2Y`, `HY_OAS`) con metadata FRED (series id, name, dimension, unit, frequency, base, amplitude).
- `FredStubMacroDataSource`: stub deterministico che implementa `IExternalMacroDataSource`; genera valori deterministici da hash SHA256 di `(seriesCode, asOf)`; `publicationDate = vintageDate = asOf` (flat); `observationDate` = `asOf` per daily, ultimo giorno del mese precedente per monthly; nessuna rete.
- `JsonMacroDataFileWriter`: implementa `IMacroDataFileWriter`; converte `FredObservation[]` in `JsonDataSnapshotRecord` (schema v1, camelCase, indentato); scrive `macro-data-{asOf:yyyy-MM-dd}.json` creando la directory se mancante; `marketObservations` serializzato come array vuoto.

### CLI - nuovo modo

- `--download-fred`: flag che attiva il modo download offline.
- Richiede `--as-of`; usa `--output-dir` per la destinazione del file.
- Compone `FredStubMacroDataSource` + `JsonMacroDataFileWriter` + `DownloadMacroDataUseCase`.
- Scrive `macro-data-{asOf}.json`; non esegue la pipeline di analisi; non scrive run/report.
- Exit `0` se OK, `1` se usage error, `2` se errore I/O o serie sconosciuta.

### Runtime - invariato

- `MacroRegime.Domain`: nessuna modifica.
- `IDataSnapshotProvider`, `JsonDataSnapshotProvider`, `JsonDataSnapshotRecord`, `JsonDataSnapshotRecordMapper`: invariati. Il file prodotto dal downloader e' letto dal provider esistente senza modifiche.
- `RunRegimeAnalysisUseCase`, `CalculateRegimeUseCase`: invariati.
- `MacroRegime.Web`: invariato, nessuna invocazione del downloader.

## Verifiche eseguite

Build:

```text
dotnet build MacroRegime.slnx --no-restore
```

Esito: build superata, 0 warning, 0 errori.

Test:

```text
dotnet test MacroRegime.slnx --no-restore
```

Esito:

- `MacroRegime.Domain.Tests`: 79 test superati;
- `MacroRegime.Application.Tests`: 27 test superati (+3 nuovi);
- `MacroRegime.Infrastructure.Tests`: 48 test superati (+16 nuovi: 4 catalog + 8 stub + 4 writer);
- `MacroRegime.Reporting.Tests`: 2 test superati;
- `MacroRegime.Cli.Tests`: 10 test superati (+3 nuovi);
- `MacroRegime.Web.Tests`: 6 test superati;
- totale: 172 test superati, 0 falliti (150 + 22 nuovi).

Smoke CLI `--download-fred`:

- comando: `--download-fred --as-of 2026-07-01 --output-dir <tmp>`;
- output: `Macro-Regime FRED download completed (stub).`, `Series: 6`, `Observations: 6`;
- file `macro-data-2026-07-01.json` generato con `schemaVersion: 1`, `asOfDate: "2026-07-01"`, 6 `macroObservations`, `marketObservations: []`;
- file leggibile da `JsonDataSnapshotProvider` strict (verificato in test `RunAsync_DownloadFred_WritesMacroDataFileReadableByJsonDataSnapshotProvider`).

Gate architetturali:

- `rg HttpClient src/MacroRegime.Domain src/MacroRegime.Application src/MacroRegime.Web` su sorgenti `.cs`: nessun match;
- nessun `HttpClient` in `MacroRegime.Infrastructure` (lo stub non usa rete);
- `MacroRegime.Domain` e `MacroRegime.Application` invariati;
- `MacroRegime.Web` invariato e senza invocazioni al downloader;
- persistenza concreta confermata come responsabilita' Infrastructure/file adapter;
- ADR 0004 formale sull'isolamento di rete.

## Documenti

- ADR: `docs/adr/0004-isolamento-rete-adapter-fred.md`.
- Spec: `docs/superpowers/specs/2026-07-10-fase-d-slice1-adapter-fred-design.md`.
- Piano: `docs/superpowers/plans/2026-07-10-fase-d-slice1-adapter-fred.md`.

## Cosa resta fuori (Slice 2 e 3)

- HTTP reale verso FRED/ALFRED, API key, retry, rate limit, errori di rete (Slice 2).
- Vintage ALFRED multi-vintage reale e selezione point-in-time avanzata (Slice 3).
- Calendario rilasci FRED reale (Slice 3).
- Provider market data esterni.
- Web UI per il download (resta operazione CLI).

## Valutazione

Fase D - Slice 1 completata. L'architettura dell'adapter FRED isolato e' in opera: porta Application `IExternalMacroDataSource`, stub Infrastructure deterministico, writer che produce file schema v1 leggibili dal runtime esistente, CLI `--download-fred` offline. Il runtime core resta senza rete, coerente con ADR 0004 e con i principi non negoziabili del progetto.

La prossima azione consigliata e' la Slice 2: client HTTP FRED reale come nuovo adapter `IExternalMacroDataSource`, senza modificare Domain/Application/Web.
