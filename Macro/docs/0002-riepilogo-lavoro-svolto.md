# Macro-Regime Engine - Riepilogo del lavoro svolto

Data: 2026-07-09

## Scopo

Questo documento riassume in ordine cronologico tutto il lavoro svolto sul progetto Macro-Regime Engine, dalla ricerca iniziale alla chiusura della prima release informativa (2026-07-08), alla Fase A di consolidamento, alla Fase B su import dati e diagnostica (2026-07-09), alla Fase C sulla decisione di persistenza locale e alla Fase D - Slice 1/2/3/4/5 sugli adapter FRED, market data esterni e dataset storico macro+market (2026-07-10). Il dettaglio di ogni passaggio e' nei documenti citati.

## Stato attuale in una frase

La prima release informativa e' completa e consolidata dalle Fasi A, B, C e D-Slice1/2/3/4/5: il sistema calcola una baseline rule-based, produce probabilita' di regime con driver e segnali contrari, genera una proposta allocativa vincolata, salva run complete (regime + allocation + data source) in JSON file-based, indicizza lo storico locale, permette di consultare e confrontare le run salvate senza rieseguire la pipeline, valida import/config con report markdown, supporta batch multi-data locale, scarica dati macro FRED con stub deterministico o client HTTP reale selezionabile da CLI usando vintage reale, dispone di un client calendario release in Infrastructure, scarica market data via stub o adapter Yahoo isolato, produce file leggibili dal runtime esistente, costruisce un dataset storico macro+market con forward returns, ed e' consultabile via CLI e Web UI read-only coperta da test. La persistenza locale file-based e' una scelta architetturale formalizzata da ADR 0003; l'isolamento di rete e' formalizzato da ADR 0004. Nessun database, nessuna rete nel runtime core.

## Cronologia del lavoro

### 1. Ricerca e impostazione (2026-06-29 / 2026-07-02)

- Studio dello stato dell'arte sulla determinazione del regime macroeconomico per l'asset allocation (`docs/research/0001-stato-arte-regime-macro.md`).
- Analisi dei progetti GitHub rilevanti per regime detection e asset allocation (`docs/research/0002-analisi-progetti-github.md`).
- Primo piano del Macro-Regime Engine con architettura funzionale a sei blocchi: data foundation, feature store, detector rule-based, state machine, reporting, research lab (`docs/planning/0001-piano-macro-regime-engine.md`).
- Piano iniziale di reimpostazione del progetto (`docs/planning/0002-piano-iniziale-reimpostazione.md`).
- Governance del progetto: ruoli, gate, decisione umana obbligatoria (`docs/planning/0003-governance-progetto.md`).
- Delivery plan con milestone 0-6 e backlog operativo (`docs/planning/0004-delivery-plan.md`).
- Proposta dei prossimi passi operativi (`docs/planning/0005-proposta-prossimi-passi.md`).

### 2. Post-mortem e restart architetturale (2026-07-02)

- Post-mortem del primo tentativo C# (prototipo Finance): classificato come reference implementation, con elenco di cosa recuperare e cosa scartare (`docs/planning/0006-postmortem-primo-tentativo.md`).
- Decisione di restart controllato: prima un core C# puro e testabile, poi persistenza, reporting e UI come adapter (`docs/planning/0007-piano-restart-architetturale.md`).

### 3. Baseline documentale pre-codice (2026-07-02)

- ADR 0001: decisione di restart architetturale (`docs/adr/0001-restart-architetturale.md`).
- ADR 0002: regole di dipendenza tra layer, dipendenze vietate e consentite (`docs/adr/0002-dipendenze-layer.md`).
- Glossario di dominio (`docs/domain/0001-macro-regime-glossary.md`).
- Mapping del prototipo Finance verso il nuovo sistema (`docs/domain/0002-prototype-mapping.md`).
- Design del domain core: value object, tipi, servizi, invarianti (`docs/domain/0003-domain-core-design.md`).
- Test plan scritto prima del codice (`docs/testing/0001-macro-regime-test-plan.md`).

### 4. Implementazione Step 1-10 (2026-07-02)

Checkpoint in `docs/checkpoints/0001` - `0012`.

- Step 1: scheletro solution e domain core con value object temporali, probabilita', score normalizzati (`0001-step1-done.md`).
- Step 4 e 6 con relativi audit: baseline rule-based detector, normalizzazione probabilita', composite score, explanation builder (`0002` - `0004`).
- Step 7: allocation domain (policy, bande, portfolio, tilt, proposal), use case applicativo di proposta allocativa, reporting allocation-aware, vertical slice `RunRegimeAnalysisUseCase`, audit finale (`0005` - `0009`).
- Step 8: adapter demo deterministici in Infrastructure (`0010-step8-demo-adapters-done.md`).
- Step 9: import locale JSON per dati macro/market con validazione schema e fallback demo controllato (`0011-step9-data-import-done.md`).
- Step 10: CLI end-to-end locale con output run JSON e report markdown (`0012-step10-cli-done.md`).

### 5. Governance locale e UI (2026-07-03 / 2026-07-06)

- Step 11: audit pre-UI (`0013-step11-pre-ui-audit.md`).
- Step 12: governance locale delle configurazioni; import JSON per model version, feature set, policy, portfolio e tilt rules con `--strict-config` (`0014`, `0015`, checkpoint di chiusura `0016`).
- Step 13: Web UI read-only con dashboard, as-of selector, probabilita', feature, explanation, allocation proposal e report (`0017-step13-plan.md`, `0018-step13-ui-done.md`).

### 6. Run manifest e chiusura release (2026-07-08)

- Step 14: manifest JSON locale delle run (`runs/manifest.json`) con upsert per as-of date; sezione `Run History` nella UI; path del manifest tra gli artifact (`0019-step14-run-manifest-done.md`).
- Chiusura della prima release informativa (`0020-first-informative-release-done.md`).

### 7. Fase A - Consolidamento storico e confronto run (2026-07-09)

Checkpoint: `docs/checkpoints/0021-fase-a-storico-confronto-run-done.md`.

- Schema run JSON portato a versione 2: il file di run ora persiste anche la proposta allocativa completa (righe per asset class, rationale, constraint) e il data source; i file v1 restano leggibili.
- `IRegimeRunStore` esteso con caricamento; il salvataggio della run e' stato spostato nell'orchestratore `RunRegimeAnalysisUseCase`, che scrive il documento completo dopo la proposta allocativa.
- Nuovo use case `LoadRegimeRunUseCase`: il dettaglio di una run storica viene letto dal JSON salvato senza rieseguire la pipeline.
- Nuovo use case `CompareRegimeRunsUseCase`: confronto tra due run salvate con delta su regime, confidence, composite score, probabilita', feature e allocazione.
- Web UI: il link `Open` della Run History apre la nuova pagina `/RunDetail` (lettura da disco); nuova pagina `/CompareRuns` per il confronto tra due date.
- Nuovo progetto `MacroRegime.Web.Tests` (5 test con `WebApplicationFactory`): la Web UI non e' piu' verificata solo con smoke manuale.

### 8. Fase B - Import dati e diagnostica (2026-07-09)

Checkpoint: `docs/checkpoints/0022-fase-b-import-diagnostica-done.md`.

- Nuovo modello diagnostico applicativo: `ValidateImportCommand`, `ImportValidationReport`, `ImportValidationItem`, `ImportValidationSeverity` e porta `IImportValidationService`.
- Adapter `JsonImportValidationService` e renderer `ImportValidationMarkdownRenderer`: validazione dei sei input locali (macro data, model, feature set, policy, portfolio, tilt rules) con severity `Ok`, `Warning`, `Error`.
- CLI `--validate-only` e `--validate-report`: produce report markdown senza eseguire la pipeline; exit code `0` se senza errori, `2` se la validazione blocca.
- CLI batch multi-data: `--batch-from`, `--batch-to`, `--data-dir`, `--portfolio-dir`; convenzione `macro-data-yyyy-MM-dd.json` e `current-portfolio-yyyy-MM-dd.json`; manifest popolato su piu' as-of date.
- Web UI: nuova pagina read-only `/ImportDiagnostics` con summary, tabella input/severity e report markdown completo.

### 9. Fase C - Decisione persistenza (2026-07-10)

Checkpoint: `docs/checkpoints/0023-fase-c-decisione-persistenza-done.md`.

ADR: `docs/adr/0003-persistenza-locale-file-based.md`.

- Valutate tre alternative: database locale immediato, file-based stabile con trigger di rivalutazione, approccio ibrido file-based + database derivato.
- Decisione presa: mantenere la persistenza locale file-based come scelta stabile per la prossima fase del progetto.
- SQLite/EF Core non viene introdotto ora; resta consentito in futuro solo come adapter Infrastructure e solo dopo nuova ADR.
- Formalizzati trigger futuri per riaprire la decisione: query storiche multi-run piu' ricche, dataset ampi, relazioni persistenti tra run/input/model version/feature set, concorrenza, decision record persistenti.
- Nessun codice applicativo modificato: la fase e' una decisione architetturale documentata.

### 10. Fase D - Slice 1 - Adapter FRED isolato con stub (2026-07-10)

Checkpoint: `docs/checkpoints/0024-fase-d-slice1-adapter-fred-stub-done.md`.

ADR: `docs/adr/0004-isolamento-rete-adapter-fred.md`.

- Nuova porta Application `IExternalMacroDataSource` e use case `DownloadMacroDataUseCase` per il download offline di dati macro.
- Nuovi tipi Application: `FredObservation`, `FredSeriesSet` (con `Baseline` di 6 serie allineate ai sample), `FredFetchCommand`, `DownloadMacroDataCommand`, `DownloadMacroDataResult`.
- Nuova porta Application `IMacroDataFileWriter` per la scrittura del file macro-data, senza riferimenti a tipi Infrastructure.
- Adapter Infrastructure `FredStubMacroDataSource`: stub deterministico che simula risposte FRED senza rete; valori derivati da hash SHA256 di `(seriesCode, asOf)`; `publicationDate = vintageDate = asOf` (flat); `observationDate` = `asOf` per daily, ultimo giorno del mese precedente per monthly.
- Adapter Infrastructure `FredSeriesCatalog`: catalogo baseline di 6 serie (`INDPRO_YOY`, `SAHM`, `T10YIE`, `VIX`, `YC_10Y2Y`, `HY_OAS`) con metadata FRED (series id, name, dimension, unit, frequency, base, amplitude e trasformazione FRED opzionale).
- Adapter Infrastructure `JsonMacroDataFileWriter`: converte `FredObservation[]` in `JsonDataSnapshotRecord` (schema v1, camelCase) e scrive `macro-data-{asOf:yyyy-MM-dd}.json` leggibile dal `JsonDataSnapshotProvider` esistente.
- CLI `--download-fred --as-of --output-dir`: modo offline che scarica (stub) i dati macro e scrive il file; non esegue la pipeline di analisi; exit `0`/`1`/`2`.
- Runtime core invariato: nessuna modifica a Domain, Application (oltre alle nuove porte/tipi), Web; `IDataSnapshotProvider` e `JsonDataSnapshotProvider` leggono i file prodotti senza modifiche.
- ADR 0004 formalizza l'isolamento di rete: downloader = adapter offline in Infrastructure, runtime = file-based, nessun `HttpClient` in Domain/Application/Web.
- Test: 22 nuovi (3 Application, 16 Infrastructure, 3 CLI); totale 172 test superati.

### 11. Fase D - Slice 2 - Client HTTP FRED reale (2026-07-10)

Checkpoint: `docs/checkpoints/0025-fase-d-slice2-fred-http-done.md`.

ADR aggiornata: `docs/adr/0004-isolamento-rete-adapter-fred.md`.

- Nuovo adapter Infrastructure `FredHttpMacroDataSource`: implementa `IExternalMacroDataSource` usando `HttpClient` e l'endpoint FRED `fred/series/observations`.
- Nuove opzioni `FredHttpMacroDataSourceOptions`: API key, base URI, tentativi, delay retry e limite osservazioni.
- La richiesta FRED usa `series_id`, `api_key`, `file_type=json`, `observation_end=asOf`, `realtime_start=asOf`, `realtime_end=asOf`, `sort_order=desc`, `limit=30`.
- Parsing robusto: ignora valori mancanti `"."`, usa la prima osservazione numerica disponibile e segnala `InvalidDataException` se non ci sono osservazioni utilizzabili.
- Retry su stati HTTP transitori (`429`, `500`, `502`, `503`, `504`).
- CLI `--download-fred` estesa con `--fred-source stub|http` (default `stub`) e `--fred-api-key` con fallback `FRED_API_KEY`.
- Se `--fred-source http` non trova una API key, la CLI ritorna usage error senza scrivere file.
- `JsonMacroDataFileWriter` serializza la source come `FRED`, valida sia per stub sia per HTTP reale.
- Test: 5 nuovi Infrastructure con `HttpMessageHandler` fake e 2 nuovi CLI; nessun test richiede Internet o una API key reale.

### 12. Fase D - Slice 3 - Vintage reale e calendario release (2026-07-10)

Checkpoint: `docs/checkpoints/0026-fase-d-slice3-vintage-calendar-done.md`.

ADR aggiornata: `docs/adr/0004-isolamento-rete-adapter-fred.md`.

- `FredHttpMacroDataSource` ora chiama `fred/series/vintagedates` prima di `fred/series/observations`.
- Per ogni serie seleziona il vintage reale piu' recente disponibile entro l'as-of (`realtime_end=asOf`, `sort_order=desc`, `limit=1`).
- La richiesta osservazioni usa `vintage_dates=<vintage selezionato>` e `observation_end=asOf`.
- `PublicationDate` e `VintageDate` nel `FredObservation` riflettono il vintage restituito da FRED/ALFRED.
- Il baseline FRED reale sostituisce il placeholder PMI/ISM con `INDPRO_YOY`, scaricato da `INDPRO` usando la trasformazione FRED `units=pc1`.
- `HY_OAS` e il normalizzatore `CREDIT_STRESS` sono allineati alla scala percentuale restituita da FRED.
- Nuovo `FredReleaseCalendarClient` in Infrastructure per calendario globale `fred/releases/dates` e calendario per singola release `fred/release/dates`.
- Nuovi tipi Infrastructure `FredReleaseCalendarOptions` e `FredReleaseDate`.
- Test senza rete: vintage, calendario release, catalogo baseline e normalizzazione scala FRED, con `HttpMessageHandler` fake.

### 13. Fase D - Slice 4 - Provider market data esterno (2026-07-10)

Checkpoint: `docs/checkpoints/0027-fase-d-slice4-market-data-yahoo-done.md`.

ADR aggiornata: `docs/adr/0004-isolamento-rete-adapter-fred.md`.

- Nuova porta Application `IExternalMarketDataSource` e nuovo use case `DownloadMarketDataUseCase`.
- Nuovi tipi Application: `MarketDataObservation`, `MarketDataSeriesSet`, `MarketDataFetchCommand`, `DownloadMarketDataCommand`, `DownloadMarketDataResult`.
- Nuova porta Application `IMarketDataFileWriter`.
- Nuovi adapter Infrastructure: `MarketDataSeriesCatalog`, `MarketDataStubDataSource`, `JsonMarketDataFileWriter`, `YahooMarketDataSource`.
- Baseline market data di 6 proxy: `SPY`, `ACWI`, `IEF`, `GLD`, `BIL`, `HYG`.
- CLI `--download-market-data --as-of --market-source stub|yahoo --output-dir`: modo offline che scrive `market-data-{asOf}.json` nello schema snapshot v1, con `macroObservations: []` e `marketObservations` popolato.
- Yahoo e' stato valutato e usato come provider pragmatico per uso personale/ricerca, ma trattato come endpoint non ufficiale e sostituibile.
- Runtime core invariato: nessuna rete in Domain/Application/Web.

### 14. Fase D - Slice 5 - Dataset storico macro+market e chiusura fase (2026-07-10)

Checkpoint: `docs/checkpoints/0028-fase-d-complete-dataset-storico-done.md`.

- Nuovo builder Infrastructure `HistoricalDatasetBuilder`.
- Nuovi record di output: `HistoricalDatasetRecord`, `HistoricalDatasetRowRecord`, `HistoricalForwardReturnRecord`.
- Nuovo comando CLI `--build-historical-dataset --dataset-from --dataset-to --macro-data-dir --market-data-dir --forward-return-days`.
- Il builder legge file locali `macro-data-yyyy-MM-dd.json` e `market-data-yyyy-MM-dd.json`, li unisce per as-of date e calcola forward returns per simbolo.
- Gli orizzonti default sono 28, 56 e 91 giorni; il comando accetta lista configurabile.
- Il calcolo usa la prima data market disponibile uguale o successiva al target dell'orizzonte, cosi' gestisce weekend/festivi quando il dataset contiene solo giorni di mercato.
- Output `historical-dataset-{from}-{to}.json`, artefatto preparatorio per Fase E.

## Verifiche allo stato attuale (dopo Fasi B, C e D-Slice1/2)

- `dotnet build MacroRegime.slnx`: build superata, 0 warning, 0 errori.
- `dotnet test MacroRegime.slnx`: 150 test superati, 0 falliti (Domain 79, Application 24, Infrastructure 32, Reporting 2, CLI 7, Web 6).
- Smoke CLI validate-only: report markdown generato con `OK: 6` e `Errors: 0`.
- Smoke CLI batch: due run generate per `2026-07-01` e `2026-07-02`, manifest popolato.
- Smoke Web: `/ImportDiagnostics?asOfDate=2026-07-01` risponde 200 e mostra `Import Validation Report`, `Macro data`, `Current portfolio`, `OK:`.
- Gate architetturali rispettati: nessuna dipendenza vietata nei layer core, nessun database, nessuna rete runtime.
- Verifica documentale Fase C: ADR 0003 e checkpoint 0023 creati, piano operativo e riepilogo aggiornati; nessun codice applicativo modificato.
- Fase D - Slice 1: `dotnet build MacroRegime.slnx` 0 errori/0 warning; `dotnet test MacroRegime.slnx` 172 test superati (Domain 79, Application 27, Infrastructure 48, Reporting 2, CLI 10, Web 6).
- Smoke CLI `--download-fred --as-of 2026-07-01`: file `macro-data-2026-07-01.json` generato con `schemaVersion: 1` e 6 `macroObservations`, leggibile da `JsonDataSnapshotProvider` strict.
- Gate Fase D: `rg HttpClient src/MacroRegime.Domain src/MacroRegime.Application src/MacroRegime.Web` nessun match nei sorgenti `.cs`; ADR 0004 rispettata.
- Fase D - Slice 2: `dotnet build MacroRegime.slnx --no-restore` 0 errori/0 warning; `dotnet test MacroRegime.slnx --no-restore` 179 test superati (Domain 79, Application 27, Infrastructure 53, Reporting 2, CLI 12, Web 6).
- Gate Fase D - Slice 2: `rg -n "HttpClient|System\.Net\.Http" src\MacroRegime.Domain src\MacroRegime.Application src\MacroRegime.Web -g "*.cs" -g "!**/bin/**" -g "!**/obj/**"` nessun match; `HttpClient` presente solo in `src/MacroRegime.Infrastructure/External/FredHttpMacroDataSource.cs`.
- Fase D - Slice 3: `dotnet build MacroRegime.slnx --no-restore` 0 errori/0 warning; `dotnet test MacroRegime.slnx --no-restore` 186 test superati (Domain 80, Application 27, Infrastructure 59, Reporting 2, CLI 12, Web 6).
- Smoke reale FRED Slice 3: `--download-fred --as-of 2026-07-01 --fred-source http` completato con 6 serie e 6 osservazioni; `INDPRO_YOY` scaricato come percent change YoY e `HY_OAS` come percentuale.
- Gate Fase D - Slice 3: nessun `HttpClient`/`System.Net.Http` nei sorgenti `.cs` di Domain/Application/Web; `HttpClient` presente solo in `src/MacroRegime.Infrastructure/External/FredHttpMacroDataSource.cs` e `src/MacroRegime.Infrastructure/External/FredReleaseCalendarClient.cs`.
- Fase D - Slice 4: `dotnet build MacroRegime.slnx --no-restore` 0 errori/0 warning; `dotnet test MacroRegime.slnx --no-restore` 206 test superati (Domain 80, Application 30, Infrastructure 73, Reporting 2, CLI 15, Web 6).
- Smoke market data Slice 4: `--download-market-data --as-of 2026-07-01` completato con 6 serie e 6 osservazioni via stub; `--download-market-data --as-of 2026-07-01 --market-source yahoo` completato con 6 serie e 6 osservazioni reali.
- Gate Fase D - Slice 4: nessun `HttpClient`/`System.Net.Http` nei sorgenti `.cs` di Domain/Application/Web; `HttpClient` presente solo in adapter Infrastructure.
- Fase D - Slice 5: `dotnet build MacroRegime.slnx --no-restore` 0 errori/0 warning; `dotnet test MacroRegime.slnx --no-restore` 211 test superati (Domain 80, Application 30, Infrastructure 76, Reporting 2, CLI 17, Web 6).
- Smoke dataset Slice 5: macro stub 6 osservazioni, market stub as-of/futuro 6+6 osservazioni, dataset storico 1 riga e 6 forward returns.

## Deviazione documentata dal piano originario

Il piano originario prevedeva una prima persistenza anche in chiave EF Core. Dopo il restart e' stata scelta consapevolmente una prima release file-based, senza database, per proteggere dominio, testabilita', as-of semantics e audit trail. La scelta e' intenzionale e tracciata nei checkpoint.

## Cosa resta fuori (non ancora fatto)

- UI/persistenza calendario release.
- Dataset reale ampio popolato su molti anni.
- Indici/manifest dedicati per dataset storici grandi.
- Database ed EF Core, non introdotti per scelta architetturale esplicita in ADR 0003.
- Dataset macro storico reale ampio.
- Backtesting, walk-forward, stress test.
- HMM, clustering, Markov switching, jump model e research lab Python.
- Autenticazione, upload file, editing configurazione da UI.
- Fiscalita' reale dettagliata, esecuzione ordini, trading automatico.

## Rischi residui noti

- I sample locali non rappresentano ancora un dataset macro storico reale.
- La diagnostica import/config e' formalizzata come report markdown, ma non ha ancora export JSON dedicato o visualizzazione grafica avanzata.
- Le run salvate prima della Fase A (schema v1) non contengono allocation e data source: restano leggibili, ma il confronto allocativo su quelle date non e' disponibile finche' la run non viene rieseguita.

## Prossimi passi

I prossimi passi sono definiti nel piano operativo consolidato: `docs/0001-piano-operativo.md`. Le Fasi A, B, C e D-Slice1/2/3/4/5 sono completate; la prossima direzione naturale e' Fase E research lab, usando il dataset storico macro+market generato dalla Fase D, mantenendo Domain/Application/Web runtime isolati dalla rete.

## Riorganizzazione documentale (2026-07-09)

Tutti i documenti markdown sono stati spostati in `docs/`, organizzati per categoria e rinominati con progressivo temporale:

- `docs/research/`: documenti di ricerca (0001-0002);
- `docs/planning/`: piani, governance, post-mortem e restart (0001-0007);
- `docs/adr/`: decisioni architetturali (0001-0004);
- `docs/domain/`: glossario, mapping e design del dominio (0001-0003);
- `docs/testing/`: test plan (0001);
- `docs/checkpoints/`: chiusure e audit degli step implementativi (0001-0026).
