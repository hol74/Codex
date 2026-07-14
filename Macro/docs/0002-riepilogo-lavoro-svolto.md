# Macro-Regime Engine - Riepilogo del lavoro svolto

Data: 2026-07-13

## Scopo

Questo documento riassume in ordine cronologico tutto il lavoro svolto sul progetto Macro-Regime Engine, dalla ricerca iniziale alla chiusura della prima release informativa (2026-07-08), alle Fasi A-D e alle prime cinque slice della Fase E (2026-07-13). Il dettaglio di ogni passaggio e' nei documenti citati.

## Stato attuale in una frase

La prima release informativa e le Fasi A-D sono complete. La Fase E dispone ora di un research lab Python separato, dataset reale 2008-2025 validato, baseline misurata, ground truth NBER e primo challenger k-means valutato con esito negativo e non promosso. Il runtime C# resta autorevole per detector e proposte allocative; Python valida e aggrega gli artefatti senza duplicare le regole. Nessun database e nessuna rete nel runtime core.

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

### 15. Fase E - Slice 1 - Research data gate (2026-07-13)

Checkpoint: `docs/checkpoints/0029-fase-e-slice1-research-data-gate-done.md`.

- Creata la struttura `research/regime-eval/`, isolata dalla solution e dal runtime C#.
- Scritto il protocollo di valutazione con dataset gate, controlli anti-leakage, walk-forward rolling 10 anni train / 2 anni test / step 1 anno e Model Gate umano.
- Implementato un loader/validatore standard-library per `historical-dataset` schema v1.
- Verificate observation, publication e availability date as-of; verificata la coerenza matematica e temporale dei forward returns.
- Implementato manifest deterministico con SHA-256, dimensione file, copertura, date mancanti, simboli e orizzonti.
- Implementato planner dei fold walk-forward; meno di 12 anni di copertura non produce fold completi.
- Aggiunta CLI Python per `validate`, `manifest` e `plan-walk-forward`.
- Aggiunti 6 test Python senza dipendenze esterne.
- Dataset reale pluriennale, challenger e metriche composite restano nelle slice successive.

### 16. Fase E - Slice 2 - Dataset reale pluriennale (2026-07-13)

Checkpoint: `docs/checkpoints/0030-fase-e-slice2-dataset-reale-pluriennale-done.md`.

- Aggiunti client bulk storici `FredHistoricalDataClient` e `YahooHistoricalMarketDataClient`, confinati in Infrastructure.
- Aggiunto `HistoricalDataPopulator` e comando CLI `--populate-historical-data` con manifest SHA-256 del corpus.
- Popolato localmente il corpus reale 2008-04-01 / 2025-12-31: 213 snapshot macro mensili e 4.536 snapshot market completi.
- Costruito dataset schema v1 con 213 righe, 3.834 forward return a 28/56/91 giorni e 6 simboli market.
- Superato il data gate point-in-time; manifest dataset SHA-256 `3cac7d9b290b149f6529fea80e326ff83f8e44abaf907eb91fb4a368099a288a`.
- Generato piano walk-forward rolling 10/2/1 con 6 fold completi.
- Le revisionabili mensili usano initial release ALFRED; `INDPRO_YOY` e `SAHM` sono ricostruiti point-in-time.
- Da aprile 2026 FRED limita `BAMLH0A0HYM2` a tre anni: per la storia lunga `HY_OAS` usa il proxy `BAA10Y`, esplicitamente marcato come `FRED:BAA10Y` nel dataset e nel manifest.
- Il validatore Python accetta il contratto macro .NET `vintageDate` oltre ad `availabilityDate`; il planner puo' ora scrivere un artefatto JSON tramite `--output`.

### 17. Fase E - Slice 3 - Baseline walk-forward (2026-07-13)

Checkpoint: `docs/checkpoints/0031-fase-e-slice3-baseline-walk-forward-done.md`.

- Aggiunto `HistoricalBaselineEvaluator`: legge il dataset schema v1, esegue il `BaselineRegimeDetector` autorevole e salva probabilita', feature, confidence, stato e warning per tutte le 213 date.
- Aggiunto comando CLI `--evaluate-historical-baseline --dataset-file`.
- Aggiunto comando Python `baseline-report`, con verifica degli hash di dataset/evaluation/piano e aggregazione deterministica sui fold.
- Metriche: confidence, soglia di conferma, quota `UncertainTransition`, transizioni operative, distribuzione regimi e rendimenti forward descrittivi per asset/orizzonte/regime.
- Aggregato sulle 84 date test uniche 2018-04-30 / 2025-03-31: confidence media 0,5417; `UncertainTransition` 57,14%; transition rate 10,84%; nessuna feature mancante.
- Primary regime aggregato: `Goldilocks` 79/84 e `DeflationBust` 5/84; regime operativo: `Goldilocks` 31, `DeflationBust` 5, `UncertainTransition` 48.
- Gli ultimi due fold risultano `UncertainTransition` al 100%, segnale di scarsa capacità discriminante o soglia/configurazione non calibrata da investigare, non da ottimizzare sul test.
- Accuracy non calcolata: manca una ground truth NBER/crisi versionata. La baseline `0.1-demo`, efficace dal 2026-07-01, e' applicata retrospettivamente e non rappresenta performance live ex-ante.

### 18. Fase E - Slice 4 - Ground truth recessiva NBER (2026-07-13)

Checkpoint: `docs/checkpoints/0032-fase-e-slice4-ground-truth-nber-done.md`.

- Versionato `research/regime-eval/ground-truth/nber-us-recessions-v1.json` con fonti NBER/FRED, policy peak/trough, periodi 2008-2009 e 2020 e limiti ex-post.
- Implementato `recession-report`: verifica hash e copertura, mappa `DeflationBust` come segnale binario e produce confusion matrix, recall/FNR, specificity/FPR, precision, accuracy, balanced accuracy, F1, date di errore e detection lag.
- Aggregato OOS su 84 date uniche: 2 mesi recessivi, 2 true positive, 3 false positive, recall 100%, precision 40%, F1 57,14%; nessun false negative.
- L'accuracy OOS 96,43% non viene usata isolatamente: la prevalenza recessiva e' solo 2,38% e rende il risultato fragile.
- Periodo completo 213 righe: primary recall 70,59%, precision 80%, F1 75%; operational recall 58,82%, precision 76,92%, F1 66,67%.
- Sulla Grande Recessione il primo `DeflationBust` arriva a settembre 2008, cinque mesi dopo il primo sample disponibile di aprile; marzo-aprile 2020 sono intercettati senza lag mensile.
- La ground truth NBER non etichetta stagflazione o stress non recessivi e non entra mai come input del detector.

### 19. Fase E - Slice 5 - Primo challenger clustering (2026-07-13)

Checkpoint: `docs/checkpoints/0033-fase-e-slice5-primo-challenger-clustering-done.md`.

- Versionata configurazione `kmeans-recession-v1`: 4 cluster, cinque feature baseline, standardizzazione e mapping cluster/NBER solo sul train, nessun hyperparameter sweep.
- Implementato k-means standard-library deterministico con inizializzazione mean-nearest/farthest-first, convergenza tracciata e cluster summary per fold.
- Aggiunto comando `clustering-report`, con hash di tutti gli input, predizioni per fold, aggregato osservazioni-fold, aggregato date uniche e delta contro la baseline.
- Test automatico: output byte-deterministico e predizioni invarianti quando cambiano solo le label test.
- Risultato OOS date uniche: TP 0, FN 2, FP 0, TN 82; recall 0%, F1 0%, balanced accuracy 50%. L'accuracy 97,62% è un artefatto della classe maggioritaria.
- Baseline sullo stesso campione: recall 100%, precision 40%, F1 57,14%, balanced accuracy 98,17%.
- Risultato osservazioni-fold: recall 25%, precision 10%, F1 14,29%; cluster mapping instabile con pochi mesi recessivi train.
- Creata model card `research/regime-eval/model-cards/kmeans-recession-v1.md`: challenger non promosso, risultato negativo conservato, vietato tuning post-hoc sugli stessi test.

### 20. Fase E - Slice 6 - Feature and Baseline Redesign (avviata 2026-07-13)

Checkpoint in corso: `docs/checkpoints/0034-fase-e-slice6-feature-baseline-redesign-in-progress.md`.

- Sospeso il passaggio diretto all'HMM: prima devono essere risolti saturazione
  delle feature e sbilanciamento della baseline `0.1-demo`.
- Aggiunto `baseline-audit`, con configurazione versionata e report deterministico
  full-history/OOS su saturazione, diversita' dei regimi, concentrazione e quota
  `UncertainTransition`.
- Aggiunto lo scenario archetipico mancante per la raggiungibilita' di
  `LateCycleOverheating`; i cinque regimi primari sono ora coperti da test Domain.
- Audit reale OOS su 84 date: 4 gate falliti. `CREDIT_STRESS` e' ai bordi nel
  95,24% delle osservazioni, i regimi primari osservati sono 2 contro un minimo
  di 3, `Goldilocks` domina il 94,05% contro un massimo dell'80% e
  `UncertainTransition` raggiunge il 57,14% contro un massimo del 50%.
- Il report negativo e' stato conservato in
  `data/historical-real-2008-2025/baseline/baseline-audit-v1-report.json`; la
  directory dati resta esclusa da Git e identificata tramite hash degli input.
- Secondo incremento: creata `1.0-candidate`, selezionabile con
  `--baseline-version v1` senza sovrascrivere la demo. Il mapping credito usa la
  scala `BAA10Y`, la curva diventa non monotona e il breakeven usa un range piu'
  sensibile con limite documentato sull'assenza di inflazione realizzata.
- Sulla candidate, saturazione credito 1,19%, 3 regimi primari e Goldilocks
  83,33%; l'incertezza peggiora al 78,57%. Il gate passa da 4 a 2 violazioni ma
  resta negativo; model card conservata e nessuna promozione.
- Terzo incremento: nuovo corpus separato con CPI YoY initial-release, momentum
  CPI e variazione trimestrale della curva. La `1.1-candidate` porta Goldilocks
  al 70,24%, Reflation al 14,29% e i gate falliti da 2 a 1; resta non promossa
  per `UncertainTransition` al 75%.
- Quarto incremento: aggiunta `1.2-candidate` con scoring archetipico e confidence
  fit/margine, congelata prima del nuovo `baseline-train-gate`. Il preflight ha
  restituito 0 fold eleggibili su 6; la candidate e' respinta senza aprire i
  report OOS. Il gate v1 ha inoltre evidenziato la necessita' di separare
  copertura aggregata e robustezza per-fold prima di una futura v1.3.
- Quinto incremento: implementato il train gate v2 con validation uniche
  aggregate per integrita'/copertura e incertezza per fold. Copertura (4 regimi,
  dominante 57,14%) e operativita' (5/6 fold) passano; integrita' fallisce per
  `RISK_APPETITE` al 27,38% contro il 25%. Nessuna apertura OOS.
- Sesto incremento: `1.3-candidate` con mapping VIX logistico preregistrato.
  Integrita' e copertura passano (`RISK_APPETITE` 1,19%), ma operativita'
  fallisce con 2/6 fold e 60,71% di incertezza aggregata. Candidate respinta e
  OOS non aperto.
- Settimo incremento: `1.4-candidate` con anchor risk/cutoff divergente tradotti
  semanticamente e confidence geometrica. Train gate 6/6; audit OOS superato con
  4 regimi e 2,38% di incertezza. NBER recall 100%, precision 20%, F1 33,33%.
  E6 chiusa tecnicamente; v1.4 baseline di ricerca non promossa operativamente.

## Verifiche allo stato attuale

- `dotnet build MacroRegime.slnx`: build superata, 0 warning, 0 errori.
- `dotnet test MacroRegime.slnx --no-restore --no-build`: 216 test superati, 0 falliti (Domain 80, Application 30, Infrastructure 81, Reporting 2, CLI 17, Web 6).
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
- Fase E - Slice 1: `python -m unittest discover -s tests -v` superato, 6 test Python; `python -m compileall -q regime_eval tests` superato.
- Fase E - Slice 2: build 0 warning/0 errori; 216 test C# superati (Domain 80, Application 30, Infrastructure 81, Reporting 2, CLI 17, Web 6); 7 test Python superati; corpus e dataset reali validati; nessuna rete nei sorgenti Domain/Application/Web.
- Fase E - Slice 3: build 0 warning/0 errori; 218 test C# superati (Domain 80, Application 30, Infrastructure 82, Reporting 2, CLI 18, Web 6); 8 test Python superati; evaluation e report baseline reali generati.
- Fase E - Slice 4: 218 test C# ancora verdi; 9 test Python superati; ground truth e report NBER reali generati con hash verificati.
- Fase E - Slice 5: 218 test C# ancora verdi; 10 test Python superati; report challenger e model card generati; k-means v1 non promosso.
- Fase E - Slice 6, primo incremento: 219 test C# superati; 11 test Python
  superati; compileall superato; audit reale generato con quattro gate falliti e
  HMM sospeso fino al redesign della baseline.
- Fase E - Slice 6, secondo incremento: build 0 errori; 226 test C# superati
  (Domain 86, Application 30, Infrastructure 83, Reporting 2, CLI 19, Web 6);
  11 test Python e compileall superati; evaluation, walk-forward, NBER e audit
  della candidate v1 generati.
- Fase E - Slice 6, terzo incremento: build 0 warning/0 errori; 231 test C#
  superati (Domain 89, Application 30, Infrastructure 85, Reporting 2, CLI 19,
  Web 6); 11 test Python e compileall superati; nuovo corpus/dataset v1.1
  validato point-in-time e quattro report candidate generati.
- Fase E - Slice 6, quarto incremento: build 0 warning/0 errori; 232 test C#
  superati (Domain 90, Application 30, Infrastructure 85, Reporting 2, CLI 19,
  Web 6); 12 test Python e compileall superati; v1.2 respinta dal train gate
  (0/6 fold eleggibili), senza apertura dei report OOS.
- Fase E - Slice 6, quinto incremento: build 0 warning/0 errori; 232 test C# e
  13 test Python superati; train gate v2 eseguito e fermato dal solo gate di
  integrita' `RISK_APPETITE`, senza apertura OOS.
- Fase E - Slice 6, sesto incremento: build 0 warning/0 errori; 234 test C#
  superati (Domain 91, Application 30, Infrastructure 86, Reporting 2, CLI 19,
  Web 6); 13 test Python e compileall superati; v1.3 respinta dal solo gate
  operativo, senza apertura OOS.
- Fase E - Slice 6, settimo incremento e chiusura: build 0 warning/0 errori;
  237 test C# superati (Domain 93, Application 30, Infrastructure 87,
  Reporting 2, CLI 19, Web 6); 13 test Python e compileall superati; train gate
  e audit v1.4 passati, report OOS/NBER generati senza tuning successivo.
- Fase E - Slice 7: preregistrato e implementato Gaussian HMM v1 train-only e
  causale; 6/6 fold convergenti. Il Model Gate lo respinge per recall 50% e F1
  11,76%, inferiori alla baseline v1.4; configurazione, report e model card sono
  conservati senza tuning post-hoc. Build 0 warning/0 errori; 237 test C# e 14
  test Python superati; compileall superato.
- Fase E - Slice 8: introdotti PredictionLedger, PredictionScore e GateDecision
  immutabili; previsione e ground truth sono fisicamente separate, le run
  registrano fingerprint del codice/runtime e le decisioni umane sono legate al
  report. Le metriche binarie sono condivise da k-means, HMM e shadow score. Un
  dry-run v1.4 su quattro mesi 2020 ha verificato il flusso; non e' shadow-live.
  Build 0 warning/0 errori; 237 test C# e 16 test Python superati; compileall e
  gate architetturale superati.
- Fase E - Slice 8, prima osservazione shadow-live: acquisizione point-in-time
  al 2026-06-30, dataset validato e ledger v1.4 congelato senza label. Il
  preflight ha bloccato un primo candidato con SAHM fermo a settembre 2025;
  aggiunto fallback tracciabile su `SAHMREALTIME` per i soli buchi della
  ricostruzione `UNRATE` e un gate che rifiuta serie mensili con oltre tre mesi
  di ritardo. Ledger SHA-256
  `7fbcae3ca6ace977e4914edbc609003fcced936228b4a29cf9f0fdac20a520fa`;
  240 test C# e 16 test Python superati.
- Fase E - stress non recessivi v1: cronologia ex-post multi-label con 6
  episodi, fonti istituzionali e controllo anti-overlap NBER. Il report v1.4
  mostra allineamento OOS 0% su financial stress/growth scare e circa 4-5% su
  inflation shock/tightening; risultato negativo conservato senza tuning. 240
  test C# e 18 test Python superati.
- Fase E9 - Shadow Operations, primo incremento: introdotti `ShadowPreflight`
  write-once, gate su mese informativo chiuso, assenza di forward return,
  freshness delle nove serie richieste e fingerprint delle sorgenti C#/Python.
  Il ciclo ledger e' idempotente sugli stessi input e rifiuta conflitti;
  `ShadowIndex` e' una vista deterministica non autorevole. L'audit
  retrospettivo di giugno passa senza modificare o ricollegare il ledger gia'
  congelato. 240 test C# e 22 test Python superati.
- Fase E9 - Shadow Operations, secondo incremento: `shadow-operations`
  orchestra population, dataset build, evaluation, preflight e freeze con
  layout mensile, stato atomico, log/hash per tentativo e recovery degli step
  completati. Lo smoke reale del 2026-07-14 rileva correttamente che non esiste
  un nuovo mese eleggibile: zero processi avviati e nessun nuovo ledger. 25 test
  Python superati; il primo ciclo prospettico resta previsto dopo luglio.

## Deviazione documentata dal piano originario

Il piano originario prevedeva una prima persistenza anche in chiave EF Core. Dopo il restart e' stata scelta consapevolmente una prima release file-based, senza database, per proteggere dominio, testabilita', as-of semantics e audit trail. La scelta e' intenzionale e tracciata nei checkpoint.

## Cosa resta fuori (non ancora fatto)

- UI/persistenza calendario release.
- Indice operativo incrementale per corpus storici grandi; il manifest deterministico e' disponibile.
- Database ed EF Core, non introdotti per scelta architetturale esplicita in ADR 0003.
- Tilt simulation con costi/turnover e stress test; la baseline descrittiva sui fold e' disponibile.
- Estensione della cronologia stress v1 con episodi nuovi e aspettative
  dimensionali: la prima versione multi-label e il report v1.4 sono disponibili.
- Serie temporale shadow-live abbastanza lunga da essere valutata: la prima
  osservazione al cutoff 2026-06-30 e' congelata, ma non e' ancora scorable.
- Markov switching e jump model; clustering e Gaussian HMM v1 sono stati
  valutati e respinti.
- Autenticazione, upload file, editing configurazione da UI.
- Fiscalita' reale dettagliata, esecuzione ordini, trading automatico.

## Rischi residui noti

- Le serie FRED finanziarie giornaliere del corpus storico usano la storia corrente, non vintage, e possono incorporare correzioni retrospettive.
- `BAA10Y` e' un proxy credit-spread long-history, non un sostituto semanticamente identico dell'high-yield OAS.
- Yahoo Finance e' un endpoint pragmatico non ufficiale e sostituibile; il corpus locale deve restare manifestato e riproducibile.
- La baseline v1.4 supera i gate tecnici con 2,38% di `UncertainTransition`, ma
  il benchmark e' gia' stato osservato e la ground truth NBER contiene solo due
  mesi recessivi OOS.
- Il Gaussian HMM v1 converge, ma la persistenza perde marzo 2020 e prolunga
  falsi segnali dopo la recessione: convergenza numerica e qualita' del modello
  restano dimensioni separate.
- La baseline `0.1-demo` e' efficace dal 2026 e il backtest 2008-2025 e' retrospettivo, non una ricostruzione di segnali storicamente operativi.
- La diagnostica import/config e' formalizzata come report markdown, ma non ha ancora export JSON dedicato o visualizzazione grafica avanzata.
- Le run salvate prima della Fase A (schema v1) non contengono allocation e data source: restano leggibili, ma il confronto allocativo su quelle date non e' disponibile finche' la run non viene rieseguita.

## Prossimi passi

I prossimi passi sono definiti nel piano operativo consolidato:
`docs/0001-piano-operativo.md`. E9.2 ha completato l'orchestrazione tecnica; il
prossimo passo non e' un nuovo tuning ma il primo ciclo prospettico `full` sul
cutoff 2026-07-31, soltanto dopo la chiusura del mese e la disponibilita' degli
input. La baseline v1.4 resta congelata e lo scoring anticipato resta vietato.

## Riorganizzazione documentale (2026-07-09)

Tutti i documenti markdown sono stati spostati in `docs/`, organizzati per categoria e rinominati con progressivo temporale:

- `docs/research/`: documenti di ricerca (0001-0002);
- `docs/planning/`: piani, governance, post-mortem e restart (0001-0007);
- `docs/adr/`: decisioni architetturali (0001-0004);
- `docs/domain/`: glossario, mapping e design del dominio (0001-0003);
- `docs/testing/`: test plan (0001);
- `docs/checkpoints/`: chiusure e audit degli step implementativi (0001-0026).
