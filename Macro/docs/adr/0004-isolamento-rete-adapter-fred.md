# ADR 0004: Isolamento di rete - adapter FRED/ALFRED offline

Data: 2026-07-10

Status: Accepted

## Contesto

La Fase D del piano operativo introduce provider dati esterni FRED/ALFRED. Il progetto ha principi non negoziabili:

- `MacroRegime.Domain` non contiene riferimenti a HTTP, database, file system o clock di sistema.
- `MacroRegime.Application` non chiama direttamente provider esterni reali.
- Il runtime core deve restare riproducibile, testabile e isolato dalla rete.

La Fase D - Slice 1 ha introdotto la porta applicativa `IExternalMacroDataSource` e uno stub deterministico `FredStubMacroDataSource` in Infrastructure, esposto tramite CLI `--download-fred`. La Fase D - Slice 2 ha aggiunto `FredHttpMacroDataSource`, client HTTP reale verso FRED, sempre confinato in Infrastructure e attivabile solo in CLI con `--fred-source http`. La Fase D - Slice 3 ha aggiunto selezione vintage reale tramite `fred/series/vintagedates` e un client calendario release `FredReleaseCalendarClient`. La Fase D - Slice 4 ha aggiunto `IExternalMarketDataSource`, `MarketDataStubDataSource` e `YahooMarketDataSource`, sempre confinati in Infrastructure e composti dalla CLI con `--download-market-data`.

Questa ADR formalizza l'isolamento di rete che vincola anche i client HTTP reali introdotti dalle Slice 2 e 3.

## Decisione

> Il runtime core (Domain, Application, Web) non ha dipendenze di rete. Il download di dati esterni e' un adapter Infrastructure invocato solo dalla CLI in modalita' offline, dietro la porta Application `IExternalMacroDataSource`. Il runtime consuma i dati tramite la porta esistente `IDataSnapshotProvider` leggendo file locali prodotti dal downloader.

### Regole

1. `MacroRegime.Domain`: nessun `HttpClient`, nessun `System.Net.Http`, nessun riferimento a provider esterni.
2. `MacroRegime.Application`: nessun `HttpClient`, nessun `System.Net.Http`. La porta `IExternalMacroDataSource` e i tipi `FredObservation`, `FredSeriesSet`, `FredFetchCommand`, `DownloadMacroDataCommand`, `DownloadMacroDataResult` vivono in Application ma non contengono logica di rete.
3. `MacroRegime.Web`: nessun `HttpClient`, nessuna invocazione del downloader. La Web UI resta read-only e consuma solo file locali.
4. `MacroRegime.Infrastructure`: unico layer autorizzato a contenere client HTTP. Le implementazioni reali sono `FredHttpMacroDataSource`, `FredReleaseCalendarClient` e `YahooMarketDataSource`; gli stub deterministici restano disponibili come adapter alternativi.
5. `MacroRegime.Cli`: unico punto di composizione dei downloader. Il modo `--download-fred` scrive `macro-data-{asOf}.json`; il modo `--download-market-data` scrive `market-data-{asOf}.json`; nessuno dei due esegue la pipeline di analisi.
6. Il file prodotto dal downloader usa lo stesso schema v1 dei sample locali ed e' letto dal `JsonDataSnapshotProvider` esistente senza modifiche.

## Alternativa considerata

### Downloader accessibile dal runtime Web

Scartata. Esporre il download nella Web UI imporrebbe rete nel runtime web, rompendo l'isolamento e la riproducibilita'. Il download resta operazione CLI offline; la Web UI consuma solo file gia' presenti.

### Porta `IExternalMacroDataSource` in Infrastructure

Scartata. Mettere la porta in Infrastructure renderebbe il use case `DownloadMacroDataUseCase` non testabile con fake Application-level e romperebbe il pattern hexagonal usato ovunque (`IDataSnapshotProvider`, `IImportValidationService`, ecc.). La porta resta in Application; le implementazioni sono adapter Infrastructure.

## Conseguenze positive

- Il runtime core resta testabile senza rete.
- La Slice 2 (HTTP reale) e' stata un puro swap dell'implementazione di `IExternalMacroDataSource`: nessuna modifica a Domain/Application/Web runtime.
- Il file `macro-data-{asOf}.json` prodotto e' immediatamente consumabile dalla pipeline esistente.
- L'audit trail resta leggibile: i dati passano sempre per file locali versionati.

## Conseguenze negative

- Il download e' una operazione esplicita separata dall'analisi: serve lanciare `--download-fred` prima di poter analizzare una nuova data con dati FRED.
- Lo stub produce valori deterministici ma non reali; per dati FRED reali serve usare esplicitamente `--fred-source http` con API key.
- Vintage reale e calendario rilasci sono disponibili a livello adapter Infrastructure; UI e persistenza dedicata del calendario restano future.

## Test di accettazione

La decisione e' rispettata se:

- `rg HttpClient src/MacroRegime.Domain src/MacroRegime.Application src/MacroRegime.Web` non matcha nessun file sorgente `.cs`;
- i csproj di Domain, Application e Web non referenziano `System.Net.Http` esplicitamente;
- `MacroRegime.Infrastructure` e' l'unico progetto autorizzato a riferimenti HTTP, oggi tramite `FredHttpMacroDataSource`, `FredReleaseCalendarClient` e `YahooMarketDataSource`;
- il modo `--download-fred` produce un file leggibile da `JsonDataSnapshotProvider`;
- la Web UI non invoca mai il downloader.

## Implicazioni operative per le prossime slice

- Slice 2 (HTTP reale): completata con `FredHttpMacroDataSource : IExternalMacroDataSource`, API key da CLI/env, retry su stati transitori; nessuna modifica a Domain/Application/Web runtime.
- Slice 3 (vintage/calendar): completata a livello adapter con selezione del vintage reale piu' recente entro l'as-of e client calendario release. Eventuali UI/persistenza del calendario restano future.
- Slice 4 (market data): completata a livello adapter con `YahooMarketDataSource : IExternalMarketDataSource`, stub deterministico, writer JSON e CLI dedicata. Yahoo e' trattato come provider non ufficiale e sostituibile.
- Ogni nuova fonte esterna macro implementa `IExternalMacroDataSource`; ogni nuova fonte esterna market implementa `IExternalMarketDataSource`; entrambe restano confinate in Infrastructure.
