# Fase D - Slice 1: Adapter FRED isolato con stub deterministico

Data: 2026-07-10

Status: Approved (design)

## Scopo

Prima slice della Fase D del piano operativo (`docs/0001-piano-operativo.md`): introdurre l'architettura dell'adapter per provider dati esterni FRED/ALFRED rispettando il vincolo non negoziabile che il runtime core non abbia dipendenze di rete. Questa slice realizza solo l'architettura e uno stub deterministico; la chiamata HTTP reale e' rimandata alla Slice 2, il vintage ALFRED reale e il calendario rilasci alla Slice 3.

## Obiettivi

1. Definire la porta applicativa `IExternalMacroDataSource` e il use case `DownloadMacroDataUseCase` che orchestrano il download offline di dati macro.
2. Implementare in Infrastructure uno stub deterministico `FredStubMacroDataSource` che simula risposte FRED senza rete, con un catalogo baseline di serie macro.
3. Produrre file `macro-data-{asOf}.json` nello stesso schema v1 gia' usato dai sample, cosicche' il runtime esistente (`JsonDataSnapshotProvider`) li legga senza modifiche.
4. Aggiungere il modo CLI `--download-fred` che esegue il download offline scrivendo il file.
5. Coprire tutto con test TDD: unit (Application), unit (Infrastructure), integrazione CLI end-to-end offline.
6. Formalizzare in ADR 0004 l'isolamento di rete: downloader = adapter offline, runtime = file-based, nessun `HttpClient` in Application/Domain/Web runtime.

## Non obiettivi (out of scope per Slice 1)

- HTTP reale verso FRED/ALFRED, API key, retry, rate limit, errori di rete (Slice 2).
- Vintage ALFRED multi-vintage e selezione point-in-time avanzata (Slice 3).
- Calendario rilasci FRED reale (Slice 3).
- Provider market data esterni: la porta `IDataSnapshotProvider` unifica macro+market ma lo stub copre solo macro; i market observations restano vuoti nel file generato (li forniscono i sample/locali).
- Web UI per il download: resta operazione CLI.

## Architettura

```text
CLI --download-fred (offline, no runtime)
   -> DownloadMacroDataUseCase (Application)
       -> IExternalMacroDataSource.FetchAsync(asOfDate, seriesSet, ct)  [porta Application]
           | implementazione stub
       -> FredStubMacroDataSource (Infrastructure, deterministico, no HTTP)
           | produce FredObservation[]
       -> FredObservationMapper -> JsonDataSnapshotRecord  (schema v1 esistente)
       -> scritta file macro-data-{asOf}.json
           v
JsonDataSnapshotProvider (esistente, invariato) legge il file a runtime
   -> CalculateRegimeUseCase (invariato)
```

### Vincoli architetturali

- `MacroRegime.Domain`: nessuna modifica.
- `MacroRegime.Application`: nessun `HttpClient`, nessuna dipendenza Infrastructure. La porta `IExternalMacroDataSource` vive in Application.Ports.
- `MacroRegime.Infrastructure`: unico layer che contiene lo stub e, in futuro, il client HTTP reale.
- `MacroRegime.Web` runtime: nessuna dipendenza di rete e nessuna chiamata al downloader.
- `MacroRegime.Cli`: unico punto in cui il downloader viene invocato (modo `--download-fred`).
- Nessuna modifica a `IDataSnapshotProvider`, `JsonDataSnapshotProvider`, `JsonDataSnapshotRecord`, `JsonDataSnapshotRecordMapper`, `RunRegimeAnalysisUseCase`, `CalculateRegimeUseCase`.

## Componenti

### Application

| Componente | File | Dettagli |
|---|---|---|
| `FredObservation` | `External/FredObservation.cs` | record: `SeriesId` (string), `SeriesCode` (string, nostro code), `ObservationDate` (DateOnly), `PublicationDate` (DateOnly), `VintageDate` (DateOnly), `Value` (decimal), `Unit` (string) |
| `FredSeriesSet` | `External/FredSeriesSet.cs` | record con lista di series codes richiesti; static `Baseline` |
| `IExternalMacroDataSource` | `Ports/IExternalMacroDataSource.cs` | `Task<IReadOnlyList<FredObservation>> FetchAsync(FredFetchCommand command, CancellationToken ct = default)` |
| `FredFetchCommand` | `External/FredFetchCommand.cs` | record: `AsOfDate AsOfDate`, `FredSeriesSet SeriesSet` |
| `DownloadMacroDataCommand` | `External/DownloadMacroData.cs` | record: `AsOfDate AsOfDate`, `FredSeriesSet SeriesSet`, `string OutputDirectory` |
| `DownloadMacroDataResult` | `External/DownloadMacroData.cs` | record: `string OutputPath`, `int SeriesCount`, `int ObservationCount` |
| `DownloadMacroDataUseCase` | `External/DownloadMacroDataUseCase.cs` | orchestratore: fetch -> scrivi file; dipende da `IExternalMacroDataSource` e da una porta di scrittura file `IMacroDataFileWriter` |

### Application (porta scrittura file)

`IMacroDataFileWriter` in `Ports/IMacroDataFileWriter.cs` con:

```csharp
Task<string> WriteAsync(IReadOnlyList<FredObservation> observations, AsOfDate asOfDate, string outputDirectory, CancellationToken cancellationToken = default);
```

`FredObservation` e' un tipo Application, quindi la porta resta nel layer Application senza riferimenti a tipi Infrastructure. Infrastructure implementa il writer convertendo `FredObservation[]` in `JsonDataSnapshotRecord` (schema v1) e serializzando JSON. Segue il pattern gia' usato per `IRegimeRunStore` (che usa `RegimeRunDocument` Application).

### Infrastructure

| Componente | File | Dettagli |
|---|---|---|
| `FredStubMacroDataSource` | `External/FredStubMacroDataSource.cs` | implementa `IExternalMacroDataSource`; usa `FredSeriesCatalog`; genera valori deterministici derivati da `asOfDate` + `seriesCode` (seed riproducibile); `publicationDate = asOf`, `vintageDate = asOf` (flat) |
| `FredSeriesCatalog` | `External/FredSeriesCatalog.cs` | mappa `SeriesCode` -> FRED series id, unita', frequenza, valore base e ampiezza; baseline di 8 serie |
| `JsonMacroDataFileWriter` | `External/JsonMacroDataFileWriter.cs` | implementa `IMacroDataFileWriter`; converte `IReadOnlyList<FredObservation>` -> `JsonDataSnapshotRecord` (schema v1, camelCase, `schemaVersion: 1`); scrive `macro-data-{asOf:yyyy-MM-dd}.json` in `outputDirectory`; crea la directory se mancante; `marketObservations` serializzato come array vuoto |

### CLI

| Componente | File | Dettagli |
|---|---|---|
| `--download-fred` mode | `src/MacroRegime.Cli/Program.cs` | nuove opzioni: `--download-fred` (flag), `--as-of`, `--output-dir`, `--series-set` (default `baseline`); compone `FredStubMacroDataSource` + `JsonMacroDataFileWriter` + `DownloadMacroDataUseCase`; scrive il file; exit `0` se OK, `2` se errore; non esegue la pipeline di analisi |

## Stub deterministico - catalogo baseline

Serie nel catalogo baseline (`FredSeriesSet.Baseline`):

| SeriesCode | FRED series id (convenzionale) | Unita' | Frequenza | Valor base | Ampiezza |
|---|---|---|---|---|---|
| `ISM_PMI` | `NAPM` | index | monthly | 52.0 | 3.0 |
| `CPI_YOY` | `CPIAUCSL` | pct | monthly | 3.0 | 1.0 |
| `UNRATE` | `UNRATE` | pct | monthly | 4.0 | 0.5 |
| `FEDFUNDS` | `FEDFUNDS` | pct | monthly | 5.0 | 0.5 |
| `GS10` | `GS10` | pct | monthly | 4.0 | 0.5 |
| `VIX` | `VIXCLS` | index | daily | 18.0 | 5.0 |
| `NFP` | `PAYEMS` | k | monthly | 150000 | 30000 |
| `RETAIL` | `RETAILA` | mom pct | monthly | 0.3 | 0.4 |

Generazione deterministica: per ogni serie, `value = base + ampiezza * f(asOf, seriesCode)` dove `f` e' una funzione deterministica (es. hash stabile di `seriesCode + asOf` normalizzato in `[-1, 1]`). `observationDate` = fine mese precedente (o `asOf` se daily). `publicationDate = asOf`, `vintageDate = asOf`.

La generazione non deve usare `Random` non seeded; usare un seed derivato deterministicamente da `(seriesCode, asOf)`.

## CLI - esempio

```text
macroregime --download-fred --as-of 2026-07-01 --output-dir ./samples
```

Output atteso:

- file `./samples/macro-data-2026-07-01.json`;
- schema `schemaVersion: 1`;
- `asOfDate: "2026-07-01"`;
- `macroObservations`: 8 elementi (uno per serie baseline);
- `marketObservations`: array vuoto;
- console: riepilogo `Wrote <path> with <n> observations`;
- exit code `0`.

## Test (TDD)

### Application - `tests/MacroRegime.Application.Tests/External/`

- `DownloadMacroDataUseCaseTests.cs`:
  - `ExecuteAsync_WritesFile_WithCorrectNameAndPath`
  - `ExecuteAsync_RequestsOnlySeriesFromSet_FromSource`
  - `ExecuteAsync_ReturnsResultWithSeriesAndObservationCounts`
  - `ExecuteAsync_PropagatesPublicationDate_AsAsOf`
  - fake `FakeExternalMacroDataSource` + fake `FakeMacroDataFileWriter` (in-memory) per testare il use case senza Infrastructure.

### Infrastructure - `tests/MacroRegime.Infrastructure.Tests/External/`

- `FredStubMacroDataSourceTests.cs`:
  - `FetchAsync_ReturnsOneObservationPerSeries_ForBaselineSet`
  - `FetchAsync_IsDeterministic_SameAsOfSameValues`
  - `FetchAsync_PublicationDate_EqualsAsOf`
  - `FetchAsync_VintageDate_EqualsAsOf_Flat`
  - `FetchAsync_Throws_OnEmptySeriesSet`
  - `FetchAsync_ReturnsOnlyRequestedSeries_WhenSubsetRequested`
- `FredSeriesCatalogTests.cs`:
  - `Baseline_ContainsEightSeries`
  - `Resolve_ReturnsMetadata_ForKnownCode`
  - `Resolve_Throws_ForUnknownCode`
- `JsonMacroDataFileWriterTests.cs`:
  - `WriteAsync_CreatesDirectory_IfMissing`
  - `WriteAsync_WritesFile_NamedMacroDataDateJson`
  - `WriteAsync_SerializesSchemaVersion1_AndCamelCase`
  - `WriteAsync_RoundTrips_ThroughJsonDataSnapshotProvider`

### CLI - `tests/MacroRegime.Cli.Tests/MacroRegimeCliTests.cs`

- `DownloadFred_WritesFileReadableByJsonDataSnapshotProvider`
- `DownloadFred_ReturnsZeroExitCode_OnSuccess`
- `DownloadFred_ReturnsNonZeroExitCode_WhenAsOfMissing`

### Web

Nessun test Web per la Slice 1: il download non e' esposto in UI.

## ADR 0004 - Isolamento di rete

Sara' scritta al termine della slice in `docs/adr/0004-isolamento-rete-adapter-fred.md` con:

- Decisione: il runtime core (Domain, Application, Web) non ha dipendenze di rete.
- Il download dati esterni e' un adapter Infrastructure invocato solo dalla CLI in modalita' offline.
- Il contratto e' la porta Application `IExternalMacroDataSource`; le implementazioni (stub ora, HTTP reale in Slice 2) sono swap senza modificare Application.
- Il runtime consuma i dati tramite la porta esistente `IDataSnapshotProvider` leggendo file locali prodotti dal downloader.
- Test di accettazione: nessun `HttpClient` in Domain/Application/Web; nessun package HTTP in quei progetti; `MacroRegime.Infrastructure` e' l'unico progetto autorizzato a riferimenti HTTP (nella Slice 2).

## Checkpoint

Al termine: `docs/checkpoints/0024-fase-d-slice1-adapter-fred-stub-done.md` con build, test count, smoke CLI `--download-fred`, e gate architetturali verificati.

Aggiornamenti finali:

- `docs/0001-piano-operativo.md`: Fase D - Slice 1 completata.
- `docs/0002-riepilogo-lavoro-svolto.md`: sezione Fase D aggiunta.

## Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Introdurre per errore `HttpClient` in Application/Domain | ADR 0004 + test gate che verificano assenza package |
| Stub con valori non deterministici (Random senza seed) | Generazione con hash deterministico di `(seriesCode, asOf)`; test determinismo |
| Dipendenza Application -> `JsonDataSnapshotRecord` Infrastructure | `IMacroDataFileWriter` accetta `IReadOnlyList<FredObservation>` (tipo Application); mapping in Infrastructure |
| File generato non leggibile dal provider esistente | Test round-trip `JsonMacroDataFileWriter -> JsonDataSnapshotProvider` |
| Bozza CLI interferisce con modalita' esistenti | `--download-fred` e' modo mutamente esclusivo come `--validate-only` |

## Criteri di completamento (Slice 1)

- Build verde, 0 warning, 0 errori.
- Tutti i test nuovi passano; test esistenti non regressi.
- `--download-fred` produce un file leggibile da `JsonDataSnapshotProvider` (smoke verificato).
- ADR 0004 scritta e accettata.
- Checkpoint 0024 scritto.
- Piano operativo e riepilogo aggiornati.
- Gate: nessun `HttpClient` in Domain/Application/Web; nessun riferimento HTTP in quei csproj.
