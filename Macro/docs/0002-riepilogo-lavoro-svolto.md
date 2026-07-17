# Macro-Regime Engine - Riepilogo del lavoro svolto

Data: 2026-07-13

## Scopo

Questo documento riassume in ordine cronologico tutto il lavoro svolto sul progetto Macro-Regime Engine, dalla ricerca iniziale alla chiusura della prima release informativa (2026-07-08), alle Fasi A-D e alle prime cinque slice della Fase E (2026-07-13). Il dettaglio di ogni passaggio e' nei documenti citati.

La descrizione organica dell'architettura corrente, delle scelte operative,
della letteratura di riferimento e del glossario e' disponibile in
`docs/architecture/0001-architettura-sistema-scelte-letteratura-glossario.md`.

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
- Consolidamento Git post-E9.2: gli artefatti runtime `.tmp` non sono piu'
  versionati. Output temporanei e chiavi ASP.NET Core Data Protection sono stati
  rimossi dall'indice preservando le copie locali. La cronologia pregressa non
  e' stata riscritta; un eventuale purge richiede un intervento separato.
- Fase E10 - Model Evidence v2 e challenger dual-timescale: introdotti gate di
  evidenza insufficiente, metriche probabilistiche/calibrazione/bootstrap,
  stress contract dimensionale v2 e un nuovo challenger causale preregistrato.
  La v1.4 resta research baseline; il dual-timescale v1 e' respinto con recall e
  F1 OOS nulli, senza tuning post-hoc. 28 test Python e 240 test C# superati.
- Fase E11.1 - Controlled Candidate Lab: congelati prima dell'implementazione
  il gate `e11-shadow-candidate-gate-v1` e tre sole configurazioni candidate.
  Il manifest write-once lega gate, input, configurazioni e validatore; vieta
  outer OOS per selezione e limita l'esito pre-prospettico a
  `shadow-candidate`. Nessun risultato dei nuovi modelli e' stato aperto. Suite
  verdi: 30 test Python e 240 test C#.
- Fase E11.2 - baseline dimensionale v1.5: implementati impulsi causali di
  crescita e stress finanziario, geometria v1.4 riusata senza modifiche,
  scenari archetipici e gate nested inner-only vincolato al manifest E11.1. La
  candidate conserva recall/F1 della v1.4 e migliora average precision di
  0,125, ma peggiora Brier di 0,00081972 e manca entrambi i mesi repo protetti;
  esito `REJECTED_FOR_SHADOW`, senza tuning post-hoc e senza outer OOS. Suite
  verdi: 32 test Python e 240 test C#.
- Fase E11.3-E11.4 - challenger e chiusura inner gate: implementati il filtro
  changepoint-duration causale con scaling robusto train-only e il rare-event
  logit L2 con standardizzazione train-only e sole tre soglie dichiarate. Il
  changepoint conserva recall ma produce 40 falsi positivi; il logit migliora
  Brier ma perde il positivo inner disponibile. Entrambi sono
  `REJECTED_FOR_SHADOW`; nessun candidato E11 passa allo shadow e l'outer OOS
  resta chiuso. Suite verdi: 35 test Python e 240 test C#.
- Fase E12.1 - event-aware data foundation: il population storico conserva ora
  massimi intramese VIX e SOFR-EFFR e drawdown massimi SPY/HYG, tutti causali e
  disponibili all'as-of. Il manifest corpus v2 conta la copertura e lascia
  esplicita l'assenza pre-SOFR. Congelato un lifecycle separato per segnale
  recessivo e stress finanziario, senza cambiare dataset schema v1 o baseline
  v1.4. Suite .NET verde: 240/240 test.
  Suite research verde: 35/35 test Python e compileall superato.
- Fase E12.2 - corpus reale e coverage freeze: generato un nuovo corpus v12
  isolato con 213 snapshot macro e 4.536 market, dataset point-in-time da 213
  righe e 6 fold. VIX max e drawdown SPY/HYG coprono il 100%; SOFR-EFFR copre
  93 mesi dal 2018 e il 100% dei test set, ma solo 0-50,4% dei train set. Il
  freeze `15eef71e961b3dd01f2dbf88` lega corpus, dataset, piano e lifecycle;
  nessun candidato o outer OOS e' stato aperto.
- Fase E12.3 - event-aware financial stress v1: formula, gate e manifest sono
  stati congelati prima dell'esecuzione. Il candidato riconosce lo shock repo,
  passa F1, Brier, ECE, durata e tutti i gate tecnici, ma viene respinto per
  recall `28,57%` e average precision `0,4661`. Lo stress bancario regionale
  2023 resta perso; zero righe outer-test e nessun tuning post-hoc.
- Fase E12.4 - SAHM yield hazard v1: candidato recessivo causale congelato e
  valutato su 84 date inner, senza outer OOS. Rileva aprile 2020 con un mese di
  ritardo e recall 50%, ma viene respinto per F1 `0,1333`, average precision
  `0,0625` e 12 mesi consecutivi di falsi positivi dopo la breve recessione.
  Nessuna policy di uscita e' stata aggiunta post-hoc.
- Fase E12.5 - decisione indipendente: congelati in un unico contratto gli
  esiti `REJECTED_FOR_SHADOW` dei due task e gli hash dei report. La fusione e'
  vietata, l'outer OOS resta chiuso e E12 termina con zero candidati shadow.
  La data foundation resta valida, mentre le due formule non saranno ritoccate
  o riutilizzate sotto gli stessi identificativi.
- Fase E13.1 - constrained candidate generation: congelata una grammatica
  task-specifica e generato un manifest write-once di 16 candidati, 8
  finanziari e 8 recessivi. ID, budget, aggregatori, persistenze e soglie sono
  fissati prima della valutazione. Tutti restano `research-generated`; nessuna
  label outer, classifica o fusione e' stata usata. Il prossimo valutatore e'
  preregistrato come leave-one-episode-out entro le sole finestre inner.
- Fase E13.2 - leave-one-episode-out: congelato il contratto di valutazione e
  applicato il LOEO agli 8 candidati finanziari su 3 episodi inner. Le varianti
  `noisy-or` coprono meglio gli eventi ma producono 56,5-78,3% di falsi allarmi
  sui controlli; `top-two-mean` scende fino a 0-8,7% ma perde almeno un
  episodio. Gli 8 recessivi sono `INSUFFICIENT_EPISODES`, perche' e'
  osservabile soltanto la recessione COVID-19. Nessuna shortlist e zero righe
  outer-test utilizzate.
- Fase E13.3 - shortlist Pareto: congelato il criterio multidimensionale e
  selezionati due estremi finanziari. `e13-financial-8ec8415452` copre 3/3
  episodi ma genera il 78,26% di falsi allarmi sui controlli;
  `e13-financial-7452a93533` limita i falsi allarmi al 4,35% ma copre 2/3
  episodi. Entrambi restano `research-shortlisted`; il ramo recessivo ha zero
  selezionati e nessuna promozione o apertura outer e' autorizzata.
- Fase E13.4 - gate assoluto: richiesti congiuntamente hit rate 100%, recall
  medio e worst-case almeno 50% e falsi allarmi non oltre 15%. Il profilo
  `coverage` fallisce solo per falsi allarmi al 78,26%; il profilo `precision`
  fallisce hit rate e recall. Entrambi sono `REJECTED_FOR_SHADOW`, il ramo
  recessivo resta fuori per evidenza insufficiente ed E13 termina con zero
  candidati eleggibili, senza outer OOS, fallback o fusione.
- Fase E14.1 - information audit: sulle 84 date inner le feature broad-market
  mostrano AUC direzionale `0,292-0,752` e forte overlap tra 7 mesi finanziari
  e 23 contrasti. Il funding spread separa il piccolo campione ma ha copertura
  solo dal 2018 e firme molto diverse tra episodi. I contrasti sono
  inflation/tightening, non veri negativi; il ramo recessivo ha un solo
  episodio. Il piano viene quindi spostato da nuove formule a tassonomia v3,
  hard negatives, feasibility storica e detector per meccanismo.
- Fase E14.2 - tassonomia tri-state e label audit: la ground truth v3 separa
  `positive`, `hard-negative`, `ambiguous` e `unlabeled`, con precedenza
  esplicita e quattro meccanismi. Il corpus contiene 6 episodi positivi, 2
  ambigui e nessun hard negative confermato; nell'inner sono osservabili solo
  3 positivi. Il gate termina `NOT_READY_FOR_CANDIDATE_GENERATION`, senza usare
  feature outer o trasformare implicitamente gli unlabeled in negativi.
- Fase E14.3 - feasibility storica: congelato un catalogo di 12 fonti con
  semantica as-of esplicita. Cinque ipotesi pre-2008 portano la copertura
  positiva teorica a 7 episodi broad-market, 3 funding, 3 banking e 5
  cross-border, ma restano zero ipotesi hard-negative. Il gate autorizza solo
  la costruzione di dossier (`GO_FOR_EPISODE_DOSSIERS_ONLY`), non popolazione,
  label, candidati o uso degli indici compositi revisionati come feature.
- Fase E14.4a - mechanism contract: congelati schema hash-bound dei dossier e
  quattro detector indipendenti con 6 feature proposte. Ogni detector separa
  `calm`, `onset`, `active` e `recovery`, usa trasformazioni causali e rinvia
  soglie e fitting a futuri fold inner LOEO. Un hard negative richiede prova
  ufficiale affermativa, corroborazione quantitativa, counterevidence e due
  reviewer. Il contratto passa, ma ground truth, corpus, composizione e
  candidati restano chiusi fino alla curation E14.4b.
- Fase E14.4b1 - dossier positivi: curate tutte le 8 coppie
  ipotesi-meccanismo pre-2008 con almeno due fonti indipendenti, narrativa
  ufficiale, osservazione quantitativa e controevidenza. I dossier sono
  deterministici, hash-bound e `reviewed`, ma non `accepted` perche' hanno un
  solo reviewer. Il mismatch tra VIX e crash 1987 e' corretto localmente con
  evidenza CFTC senza riscrivere il catalogo congelato. Restano zero hard
  negative: ground truth, corpus e candidati rimangono chiusi.
- Fase E14.4b2 - hard negative e review queue: curati quattro contrasti con
  prova affermativa, uno per ciascun meccanismo. Brexit 2016 fornisce i
  contrasti broad-market, funding e cross-border; la crisi messicana 1994-95
  fornisce il contrasto banking-credit. Tutti i 12 dossier sono manifestati in
  una coda hash-bound. Lo schema delle ricevute richiede un reviewer diverso
  dall'autore e il codice rifiuta esplicitamente l'auto-accettazione. Poiche'
  non esistono ancora ricevute indipendenti, l'esito e'
  `INDEPENDENT_REVIEW_REQUIRED` e nessuna label viene promossa.
- Fase E14.4b3a - external review handoff: generato un bundle immutabile con
  12 copie dossier byte-identiche, 12 worksheet, 12 template di ricevuta e 36
  occorrenze di locator. I template sono intenzionalmente non ingeribili prima
  della compilazione e devono essere copiati fuori dal bundle. L'audit termina
  `AWAITING_EXTERNAL_REVIEW`: l'handoff e' pronto, ma nessuna review e' stata
  attribuita al generatore e la label foundation resta chiusa.
- Fase E14.4b3b - independent review ingestion: un reviewer agente distinto
  ha aperto le fonti e restituito 12 ricevute. Otto dossier sono `accept`,
  quattro `needs-revision` e nessuno e' `reject`. Continental Illinois non ha
  un end boundary luglio sufficientemente provato; i tre dossier Messico non
  dimostrano il confine marzo 1995 e il locator FDIC del controllo banking non
  e' direttamente renderizzabile. Lo schema v2 rappresenta onestamente fonti
  non accessibili nei non-accept, mantenendo requisiti stretti per `accept`.
  Il gate termina `DOSSIER_REVISIONS_REQUIRED`; gli 8 hash accettati sono
  preservati e nessuna label o candidato viene autorizzato.
- Fase E14.4b4 - targeted dossier revision: revisionati soltanto Continental
  Illinois e i tre dossier Messico. Continental termina ad agosto con
  stabilizzazione documentata a settembre; il broad-market Messico mantiene
  marzo grazie alla successiva ripresa di aprile; il cross-border si estende a
  giugno; il banking hard-negative usa il QBP FDIC 1995 Q1 direttamente
  accessibile. Gli 8 dossier accettati restano byte-identici. Il reviewer
  distinto ha accettato tutti i 4 nuovi hash; l'ingestione produce 12/12
  accettazioni e `READY_FOR_LABEL_FOUNDATION_GATE`. Nessuna label, ground truth
  o candidato e' stato ancora scritto: E14.4c resta un gate separato.
- Fase E14.4c - label-foundation gate: i 12 dossier accettati sono stati
  trasformati in una proposta versionata con 42 label mese-meccanismo su 24
  mesi. Non emergono conflitti nello stesso meccanismo ne' con la tassonomia
  v3; quattro mesi del Messico preservano correttamente il contrasto tra stato
  positivo broad/cross-border e hard-negative banking. La copertura positiva
  combinata raggiunge 11 episodi indipendenti e supera tutte le soglie per
  meccanismo. I quattro dossier hard-negative derivano invece da due soli
  eventi indipendenti (Brexit e Messico), quindi producono 2 eventi totali e 1
  per meccanismo contro soglie 6/2. Lo stato e'
  `FOUNDATION_MERGE_READY_MORE_EVIDENCE_REQUIRED`: e' autorizzabile soltanto
  una tassonomia v4 versionata; ground truth v3 e candidati restano immutati e
  chiusi fino a nuova evidenza hard-negative.
- Fase E14.4d - taxonomy v4: la proposta E14.4c e' stata materializzata in
  `us-financial-stress-mechanism-aware-v4` senza modificare la v3. Le 12 nuove
  voci restano monomeccanismo per non appiattire confini diversi; ogni voce ha
  un `independentEventId`, per cui i tre dossier Brexit valgono un solo evento
  e le tre manifestazioni Russia/LTCM un solo positivo indipendente. La
  cronologia parte da maggio 1984 e conserva il limite ereditato a dicembre
  2025. L'audit conferma zero conflitti, 11 positivi e 2 hard-negative
  indipendenti. Lo stato e'
  `TAXONOMY_V4_VERSIONED_MORE_HARD_NEGATIVES_REQUIRED`: la tassonomia e'
  versionata, ma candidati, outer OOS e promozione restano chiusi.
- Fase E14.4e - hard-negative expansion: curati quattro contrasti basati su
  eventi indipendenti e fonti istituzionali: crash azionario 1987 come
  hard-negative banking-credit, repricing 2018Q4 come hard-negative funding,
  repo stress 2019 come hard-negative cross-border e regional bank stress
  2023 come hard-negative broad-market. Gli stati misti cross-meccanismo sono
  intenzionali e non producono conflitti sulla chiave `(mese, meccanismo)`.
  La queue v6 preserva byte-identici i 12 manifest accettati e aggiunge 4
  dossier `reviewed` in attesa. Se tutti fossero accettati, la copertura
  salirebbe da 2 a 6 eventi hard-negative indipendenti e da 1 a 2 per ciascun
  meccanismo. Questo e' solo un risultato potenziale: lo stato resta
  `INDEPENDENT_REVIEW_REQUIRED`; tassonomia v4, candidati e outer OOS non sono
  stati modificati. E14.4f deve produrre l'handoff immutabile e acquisire
  ricevute indipendenti sui quattro nuovi hash. La regressione finale supera
  81/81 test Python, la compilazione bytecode e 240/240 test .NET net10.0.
- Fase E14.4f - expansion review handoff: costruito un bundle immutabile che
  contiene soltanto i quattro hard negative E14.4e. I 12 dossier accettati
  precedenti sono esclusi e non riaperti. Il bundle contiene 4 copie dossier
  byte-identiche, 4 worksheet, 4 template schema v2 intenzionalmente non
  ingeribili e 12 occorrenze di locator. Il contratto vieta review e
  ingestione al generatore, oltre a tassonomia, candidati e outer OOS. Lo
  stato e' `EXPANSION_AWAITING_EXTERNAL_REVIEW`: la copertura potenziale non
  e' diventata accettata e le ricevute indipendenti restano zero. E14.4g deve
  validare decisioni esterne legate esattamente ai quattro hash dell'handoff.
  La regressione supera 84/84 test Python, la compilazione bytecode e 240/240
  test .NET Debug/net10.0.
- Fase E14.4g - expansion review ingestion: implementato un gate schema v2
  che accetta soltanto ricevute sui quattro hash E14.4f e preserva byte-identici
  i 12 accept precedenti. Un `accept` richiede fonti aperte, claim e confini
  supportati, controevidenza considerata e nessun output di modello. A
  differenza del vecchio flusso, un run incompleto non scrive una queue
  parziale: produce soltanto un audit retry-safe; la queue v7 nasce dopo
  quattro ricevute valide. Il run reale trova 0/4 ricevute e termina
  `EXPANSION_REVIEW_INCOMPLETE`; queue v7, coverage gate, tassonomia e
  candidati restano assenti o chiusi. Il prossimo input deve provenire da un
  reviewer indipendente, poi lo stesso comando potra' essere rieseguito con
  nuovi output immutabili. La regressione supera 87/87 test Python, la
  compilazione bytecode e 240/240 test .NET Debug/net10.0.
- Fase E14.4g - independent expansion review completata: un reviewer distinto
  ha aperto tutti i 12 locator e prodotto quattro ricevute schema v2. Sono
  accettati il contrasto banking-credit del crash 1987 e il contrasto funding
  del repricing 2018Q4. Il dossier regional-bank 2023 richiede revisione per
  il locator IMF `text.ashx` non direttamente accessibile; il dossier repo
  2019 richiede revisione perche' le fonti dimostrano spillover repo esteri
  limitati, ma non lo stato del meccanismo di crescita cross-border. La queue
  v7 preserva i 12 accept precedenti e registra 2 nuovi accept, 2
  `needs-revision`, zero reject. Lo stato e'
  `EXPANSION_DOSSIER_REVISIONS_REQUIRED`: E14.4h, tassonomia e candidati
  restano chiusi. La revisione successiva deve riguardare soltanto i due hash
  non accettati.
- Fase E14.4g2 - targeted expansion revision: preservati i 14 accept e
  revisionati soltanto i due hash non accettati. Il regional-bank 2023 e'
  stato accettato dopo la sostituzione del locator IMF `text.ashx` con il PDF
  ufficiale accessibile. Il repo 2019 e' stato ritirato, perche' misurava
  funding estero e non crescita reale, e sostituito dal Flash Crash 2010.
  La prima rilettura del sostituto ha restituito `needs-revision` per un PDF
  CPB indicizzato ma HTTP 404; il gate e' rimasto correttamente chiuso. Una
  seconda revisione ha usato la pagina CPB live e verificato il relativo XLS:
  indice world trade 154,0 ad aprile e 157,4 a maggio (circa +2,2%), oltre a
  crescita Q2 circa +3,4%. Il reviewer indipendente ha emesso `accept`.
  Queue v11 e audit mirato v2 registrano 16/16 accept, 6 eventi hard-negative
  indipendenti e 2 per ciascun meccanismo. Lo stato e'
  `READY_FOR_HARD_NEGATIVE_COVERAGE_GATE`: autorizza E14.4h, ma non muta
  tassonomia v4 e non apre ancora candidati o outer OOS. La regressione finale
  supera 94/94 test Python, compilazione bytecode e test .NET.
- Fase E14.4h - accepted hard-negative coverage gate: introdotto un gate
  read-only e hash-bound che risolve 16/16 manifest accettati, protegge i 12
  dossier gia' presenti nella tassonomia v4 e considera nuovi soltanto i
  quattro dossier non ancora materializzati. Gli eventi sono contati per
  `hypothesisId`, non per dossier: la copertura passa da 2 a 6 hard negative
  indipendenti e raggiunge esattamente 2 eventi per ciascuno dei quattro
  meccanismi. Restano 11 positivi, zero conflitti `(mese, meccanismo)` e stati
  misti cross-meccanismo intatti. Lo stato e'
  `ACCEPTED_HARD_NEGATIVE_COVERAGE_READY`. Il gate autorizza soltanto una
  proposta/versione di tassonomia v5; non ha scritto label, mutato la v4,
  generato candidati, letto outer OOS o autorizzato promozioni. La regressione
  completa supera 97/97 test Python, compilazione bytecode e test .NET.
- Fase E14.4i - taxonomy v5 accepted expansion materialization: creati schema,
  contratto hash-bound e materializzatore write-once per una nuova tassonomia
  `us-financial-stress-mechanism-aware-v5`, lasciando byte-identica la v4. I
  quattro dossier hard-negative accettati sono stati aggiunti come episodi
  monomeccanismo con `hypothesisId` quale identita' indipendente e provenienza
  completa verso dossier, queue e coverage gate. La v5 contiene 16 evidenze
  di fondazione, 11 episodi positivi e 6 hard negative indipendenti; ciascun
  meccanismo dispone di 2 hard negative e non risultano conflitti
  `(mese, meccanismo)`. Lo stato
  `TAXONOMY_V5_VERSIONED_CANDIDATE_READINESS_REQUIRED` autorizza soltanto il
  successivo gate E14.4j: candidate generation, outer OOS e promozione restano
  false. La regressione completa supera 99/99 test Python, compilazione
  bytecode e test .NET.
- Fase E14.4j - candidate-readiness gate: introdotti un contratto hash-bound,
  un audit write-once e un comando CLI che separano la validita' informativa
  della tassonomia dalla prontezza operativa della generazione. Il gate reale
  conferma che tassonomia v5, copertura, conflitti e quattro detector sono
  coerenti, ma termina
  `CANDIDATE_READINESS_BLOCKED_FOUNDATION_AND_PROTOCOL`. Le sei feature dei
  detector risultano ancora `proposal-not-populated` e manca una foundation
  point-in-time materializzata. Inoltre il protocollo E13 e' legato al lock
  E12 e descrive due task aggregati, non quattro detector indipendenti. I
  controlli E13 causali, train-only, missingness-explicit e inner-only restano
  riusabili, ma nessun candidato e' stato generato e outer OOS/promozione
  restano chiusi. Il piano e' stato esteso con E14.4k per la feature foundation
  ed E14.4l per il nuovo protocollo taxonomy-v5-bound. La regressione completa
  supera 102/102 test Python, compilazione bytecode e test .NET.
- Fase E14.4k - mechanism feature foundation: scaricati e congelati tramite
  SHA-256 gli snapshot ufficiali Cboe VIX, FRED BAA10Y/TEDRATE/DTWEXB e il
  workbook aggregato FDIC Q4 2025. Il materializzatore produce cinque serie e
  sei binding per i quattro detector: 432 mesi VIX, 480 BAA10Y, 433 TEDRATE,
  300 DTWEXB e 167 trimestri FDIC, per 1.812 osservazioni complessive e zero
  record oltre il cutoff 2025-12-31. TEDRATE e DTWEXB terminano ai confini di
  metodologia documentati; FDIC usa un lag conservativo di 60 giorni e il Q4
  2025 resta escluso perche' non disponibile al cutoff. Foundation, lock e
  audit sono write-once e hash-bound. Lo stato
  `FEATURE_FOUNDATION_MATERIALIZED_WITH_VINTAGE_LIMITATIONS` esplicita che le
  storie daily FRED e il workbook FDIC sono snapshot correnti, non vintage
  perfette. E14.4l puo' progettare il protocollo research a quattro detector,
  ma candidate generation, outer OOS e promozione restano chiusi. La
  regressione completa supera 105/105 test Python, compilazione bytecode e test
  .NET.
- Fase E14.4l - four-detector candidate protocol: congelati schema, protocollo
  e readiness contract legati tramite hash alla tassonomia v5, alla feature
  foundation e al relativo lock. La grammatica E13 a due task e' stata
  sostituita con quattro grammatiche indipendenti e dieci profili: 16 candidati
  broad-market, 4 funding, 16 banking e 4 cross-border, per un budget massimo
  di 40. Le soglie sono quantili selezionabili esclusivamente nei train inner
  dei fold leave-one-episode-out; persistenza di ingresso e recovery restano
  separate. Il protocollo richiede metriche positive e hard-negative per
  meccanismo e non considera i mesi unlabeled come negativi. Lo stato reale
  `RESEARCH_CANDIDATE_GENERATION_READY_OUTER_OOS_CLOSED` autorizza soltanto la
  futura generazione deterministica del manifest E14.5. Fitting, evaluation,
  composizione cross-meccanismo, outer OOS e promozione restano falsi. I limiti
  vintage sono accettati solo per ricerca e richiederanno sensitivity gate
  prima di qualunque promozione. La regressione completa supera 108/108 test
  Python, compilazione bytecode e test .NET.
- Fase E14.5 - deterministic candidate manifest: creati schema e contratto di
  generazione hash-bound, un generatore write-once e il comando
  `e14-generate-candidates`. La run reale produce esattamente 40 configurazioni
  con ID deterministici: 16 banking-credit, 16 broad-market-repricing, 4
  cross-border-growth e 4 funding-liquidity. Ogni candidato lega meccanismo,
  detector, profilo, feature binding inner-only, quantili selezionabili nel
  train inner e persistenze di ingresso/recovery. Lo stato
  `GENERATED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED` certifica che il manifest
  e' stato generato senza leggere label o dataset e senza applicare transform,
  fitting, evaluation, ranking o composizione. Outer OOS e promozione restano
  chiusi; il passo successivo e' la preregistrazione E14.6 del protocollo LOEO
  inner per meccanismo. La regressione completa supera 111/111 test Python,
  compilazione bytecode e test .NET.
- Fase E14.6 - preregistrazione LOEO e structural-coverage gate: congelate le
  regole leave-one-independent-positive-episode-out, la selezione dei quantili
  solo sui train, le metriche per meccanismo e il divieto di usare mesi
  unlabeled come negativi. Prima del fitting e' stata verificata
  l'osservabilita' con 60 mesi minimi di storia e senza carry oltre i confini
  metodologici. Solo i 16 candidati broad-market risultano eleggibili; i 16
  banking, i 4 cross-border e i 4 funding sono strutturalmente ineligibili.
  Lo stato `INNER_LOEO_PREREGISTERED_STRUCTURAL_COVERAGE_BLOCKED` mantiene
  chiusi sia fitting globale sia fitting parziale, oltre a evaluation, ranking,
  composizione, outer OOS e promozione. Il prossimo passo E14.6a deve riparare
  o ridisegnare esplicitamente la copertura informativa, non aggirare il blocco.
  La regressione completa supera 114/114 test Python, compilazione bytecode e
  test .NET.
- Fase E14.6a - coverage repair preregistration: respinta la riduzione post-hoc
  dei 60 mesi e congelato un percorso a tre fonti standalone. Banking-credit
  usa come proposta la severita' mensile delle transazioni FDIC di
  fallimento/assistenza dal 1934; cross-border usa la variazione assoluta del
  broad dollar mensile `TWEXBMTH` dal 1973 senza splice oltre il 2019; funding
  usa Fed funds meno T-bill, derivato da `TB3SMFFM`, dal 1954. I subindex NFCI
  restano diagnostici perche' sono ristimati e revisionati. La proiezione
  strutturale raggiunge 28 candidati: 16 broad preservati e 4 nuovi per ciascun
  meccanismo riparato. Lo stato
  `STRUCTURAL_COVERAGE_REPAIR_PREREGISTERED_MATERIALIZATION_REQUIRED`
  autorizza soltanto E14.6b, cioe' download, freeze e foundation v2; candidate
  generation, fitting, evaluation e outer OOS restano chiusi. La regressione
  completa supera 117/117 test Python, compilazione bytecode e test .NET.
- Fase E14.6b - feature foundation v2: scaricati e congelati gli snapshot
  ufficiali FDIC failures/assistance, `TWEXBMTH` e `TB3SMFFM`; foundation v1
  e lock v1 sono rimasti hash-bound e immutati. La v2 attiva cinque serie:
  due broad riportate per contenuto esatto e tre replacement, per 3.437
  osservazioni complessive. L'inventario FDIC contiene 4.115 record; 154 record
  senza `QBFASSET` producono 69 mesi missing espliciti e 556 mesi senza
  transazioni sono zeri osservati solo dopo la verifica di completezza API.
  La copertura reale positiva/hard-negative e' 3/2 banking, 6/2 broad, 5/2
  cross-border e 3/2 funding. `TWEXBMTH` termina senza splice nel 2019 e la
  diagnostica `TB3SMFFM` separa 774 mesi pre-confine da 84 post-confine senza
  dichiararne l'equivalenza. La riparazione strutturale e' riuscita, ma
  `strictVintageReady` resta falso perche' mancano snapshot point-in-time
  comparabili; generation, fitting, evaluation e outer OOS restano chiusi.
  La regressione completa supera 120/120 test Python.
- Fase E14.6c - readiness gate v2: costruito un roster hash-bound di 28
  ingressi applicando 60 osservazioni non-missing, lag `availableOn` derivato
  dalle serie e divieto di carry sul calendar slot missing. Tutti gli ingressi
  risultano eleggibili: 16 ID broad v1 preservati esattamente, 24 ID v1
  ritirati e 12 nuovi ID v2 pianificati, quattro per banking, cross-border e
  funding. Il roster non e' un candidate manifest e nessun candidato e' stato
  generato o fittato. La sensitivity funding 2019 richiede in futuro soglie,
  shift IQR, alert rate e metriche episodio pre/post, ma il segmento pre-2019
  non e' usato come gate alternativo perche' contiene un solo positivo funding.
  Lo stato autorizza soltanto la progettazione del protocollo v2; manifest,
  fitting, evaluation, ranking e outer OOS restano chiusi. La regressione
  completa supera 123/123 test Python.
- Fase E14.6d - candidate protocol v2: congelato il protocollo sui 28 ID del
  roster nello stesso ordine, senza ricalcolarli. La grammatica contiene 7
  profili e le quattro combinazioni entry/recovery per ciascuno; preserva 16 ID
  broad, usa i 12 ID v2 e mantiene vietati i 24 ID ritirati. Il futuro manifest
  deve copiare verbatim profili, feature binding ed eligibility, variando solo
  il lifecycle. As-of semantics, lag, missingness, sensitivity funding 2019 e
  rischio di revisione current-history sono parti vincolanti del protocollo.
  E' autorizzata soltanto la futura materializzazione del manifest v2; fitting,
  evaluation, ranking e outer OOS restano chiusi. La regressione completa
  supera 126/126 test Python.
- Fase E14.6e - candidate manifest v2: materializzato in modo write-once il
  manifest hash-bound di 28 candidati, con distribuzione 4 banking, 16 broad,
  4 cross-border e 4 funding. Ordine e ID coincidono con roster e protocollo;
  profili, binding, persistenza, eligibility e identity policy sono copiati
  verbatim. L'unica modifica ammessa e osservata e' il lifecycle da
  `readiness-planned-not-generated-not-fit` a `research-generated-not-fit`.
  L'audit registra zero feature trasformate e zero righe outer; fitting,
  evaluation, ranking, composizione e promozione restano chiusi. La regressione
  completa supera 129/129 test Python.
- Fase E14.6f - preregistrazione LOEO v2: verificata l'intera catena hash-bound
  da taxonomy, foundation/lock/audit v2, protocollo/audit v2 e manifest/audit
  v2. Tutti i 28 candidati sono eleggibili e sono state congelate 140
  assegnazioni candidato-episodio: 12 banking, 96 broad, 20 cross-border e 12
  funding. Sono preregistrati trasformazioni causali e soglie q80/q90/q95 sui
  soli training row, gate assoluti indipendenti per meccanismo, sensitivity
  funding sul confine 2019 e controllo obbligatorio dello snapshot drift.
  Il passo autorizza trasformazioni, fitting e valutazione inner-only in
  E14.6g, ma non li esegue; ranking, composizione, outer OOS e promozione
  restano chiusi. La regressione completa supera 132/132 test Python.
- Fase E14.6g - fitting e valutazione LOEO v2: eseguiti i 140 fold
  preregistrati sui 28 candidati con percentile causale midrank, esclusione
  dell'episodio held-out dalla storia di fit, missingness che interrompe la
  persistenza e soglie q80/q90/q95 selezionate sui soli training score. La
  sensitivity funding produce 12 report completi full/pre-2019. Nessun
  candidato supera tutti i gate: il migliore banking raggiunge hit rate 0,667,
  mean recall 0,50 e hard-negative alert 0,067, ma worst recall resta zero;
  broad, cross-border e funding raggiungono hit rate massimo 0,167, 0,40 e 0.
  Il limite dominante e' quindi la generalizzazione positiva tra episodi, non
  il tasso di falsi allarmi sui controlli. Ranking, shortlist, composizione,
  outer OOS e promozione non sono autorizzati. La regressione completa supera
  136/136 test Python.
- Fase E14.6h - diagnosi no-go: decomposto senza rieseguire candidati il report
  E14.6g per gate, episodio, profilo e persistenza. Nessun candidato fallisce
  il gate hard-negative alert o threshold range, mentre tutti hanno worst
  episode recall zero. Banking manca completamente euro-sovereign 2011; broad
  manca 5 episodi su 6 e intercetta soltanto Russia/LTCM 1998; cross-border
  manca China/EME, Russia/LTCM e taper tantrum; funding manca tutti i tre
  positivi. La famiglia v2 e' chiusa con no-go e non puo' essere recuperata con
  ranking relativo, rilassamento gate o retuning. E' autorizzato soltanto E14.7,
  cioe' il design preregistrato di nuove firme informative complementari per
  meccanismo; taxonomy, materializzazione, fitting, evaluation, composizione e
  outer OOS restano chiusi. La regressione completa supera 139/139 test Python.
- Fase E14.7 - nuova ipotesi informativa: preregistrato un piano hash-bound con
  8 famiglie finite, 10 fonti e 17 firme episodio-specifiche che separano
  onset, intensita' e recovery. Il piano introduce deterioramento e flussi di
  bilancio bancari, drawdown e dispersione creditizia, dollar shock e flussi
  bancari BIS, tiering commercial paper e dislocazione repo. Ogni famiglia ha
  direzione, trasformazione, missingness, regime metodologico, falsification
  condition e ablation congelati. L'audit reale ha SHA-256
  `4da83787c02b1f8af5f751234fa6805fe75d6e1ff2ce8092056118ac45ad6cae`;
  autorizza soltanto E14.7a, un audit di fattibilita' source/vintage. Nessun
  dato e' stato acquisito e tutti i gate modellistici e outer restano chiusi.
- Fase E14.7a - source/vintage feasibility: verificati soltanto metadati e
  condizioni dei provider, senza scaricare osservazioni. Su 10 fonti, 1 e'
  `ready`, 5 sono `conditional` e 4 `blocked`; sulle 8 famiglie il risultato e'
  0 `ready`, 3 `conditional` e 5 `blocked`. I blocchi includono licenze
  Nasdaq/Moody's, volume CP storico incompleto e storia causale insufficiente:
  4/60 mesi FDIC per Continental Illinois, 19/60 commercial paper per
  Russia/LTCM e 17/36 SOFR per repo-stress 2019. H.8 e le due famiglie BIS
  restano condizionali a prova vintage/release. L'audit SHA-256 e'
  `5851dac52554a0885e93cadcac33de68f92b418911f12ad36f61c68b392329b1`;
  acquisizione e modellazione restano chiuse e il solo passo autorizzato e'
  E14.7b, preregistrazione della remediation.
- Fase E14.7b - remediation di fattibilita': preservate esattamente le 3
  famiglie condizionali con i rispettivi task documentali e ritirate senza
  fallback le 5 famiglie bloccate. Sono state preregistrate 5 sostituzioni
  indipendentemente motivate su 7 fonti ufficiali: fragilita' bancaria storica
  FDIC, market value equity Z.1, dislocazione Treasury DGS2/DGS10, tiering
  DCD90-DTB3 e bilancio repo dei primary dealer New York Fed. Tutte superano il
  controllo nominale della storia causale minima, ma non sono dichiarate
  `ready`: serve E14.7c per provare accesso, licenza, vintage, release e regimi
  metodologici. L'audit reale ha SHA-256
  `275cd32b58d12829e46542930be44fe1589931814c95c39a1be138c93b6b47a3`.
  Nessuna osservazione e' stata scaricata, nessun LOEO/outer e' stato usato per
  scegliere le sostituzioni e acquisizione, foundation e modellazione restano
  chiuse. La regressione completa supera 150/150 test Python.
- Fase E14.7c - re-audit source/vintage: riesaminate con evidenza
  provider-primary le 3 famiglie preservate e le 5 sostituzioni, senza
  scaricare osservazioni. Solo `fred-dtb3` resta `ready`; le altre 9 fonti e
  tutte le 8 famiglie sono `blocked`. Il limite dominante e' la disponibilita'
  event-time: H.8 non prova release pre-1984, l'archivio online Z.1 parte nel
  1996, ALFRED documenta i metadati H.15 dal 2005, BIS non espone vintages
  storici completi e FDIC/NY Fed non chiudono snapshot, revisioni e termini.
  La lunga copertura nominale non e' stata accettata come sostituto della
  causalita'. L'audit reale SHA-256 e'
  `7dcfaa24e9df9c46f0e0ddfd499acf4eeab8f5343c85b970ddf268a7e0c36413`;
  autorizza soltanto E14.7d, una decisione preregistrata sulla politica dei
  vintages. Acquisizione e modellazione restano chiuse. La regressione completa
  supera 154/154 test Python.
- Fase E14.7d - decisione vintage policy: confrontate senza dati o score la
  chiusura E14, la ricostruzione archivistica e uno scope post-2005 separato.
  Selezionato condizionalmente lo scope con cutoff `2006-01-01`; il legacy E14
  resta chiuso e la ricostruzione provider-primary e' conservata solo come
  backlog finanziato. Lo scope trattiene 6 positivi unici e 10 assegnazioni,
  con conteggi banking 2, broad 4, cross-border 2 e funding 2. I controlli
  post-cutoff sono invece 0/2/2/2: mancano 2 hard negative banking-credit e lo
  scope non puo' ancora attivarsi. L'audit reale SHA-256 e'
  `98af6a7b301240d2ff9ba763dc1f4e579676774361237dc1c61296e1c64eda69`;
  autorizza soltanto E14.7e, design di scope/fonti e controlli banking senza
  mutare taxonomy o acquisire osservazioni. La regressione supera 158/158 test.
- Fase E14.7e - fattibilita' scope post-2005: congelati due nuovi candidati
  hard-negative banking-credit, London Whale 2012 e Archegos 2021. Sono eventi
  distinti dai positivi, senza sovrapposizioni temporali, con evidenza evento
  provider-primary ed evidenza indipendente di contenimento sistemico. I
  conteggi diventano 2/2/2/2 hard negative contro 2/4/2/2 positivi. Il nuovo
  audit non eredita automaticamente le famiglie bloccate E14.7c e identifica
  una famiglia source/vintage `ready` per meccanismo: H.8/QBP per banking,
  DGS2-DGS10 per broad, H.10 per cross-border e DCPF3M-DTB3 per funding. Audit
  SHA-256 `0b4869ed5a774248b7223b41ac7e49d1624587bb2536857536eeb8e1736b27bd`.
  E' autorizzata soltanto E14.7f, proposta taxonomy separata con dossier e
  queue di review indipendente; scope, dati, foundation e modelli restano
  chiusi. La regressione completa supera 162/162 test Python.
- Fase E14.7f - proposta taxonomy post-2005: materializzata la proposta
  inattiva `us-financial-stress-post2005-v1` con identificatori nuovi e soli
  riferimenti hash-bound alla taxonomy v5. La proposta contiene 6 episodi
  positivi post-cutoff, 6 righe hard-negative legacy e 2 nuovi controlli
  banking-credit. London Whale e Archegos sono rappresentati da dossier
  reviewed ma non accepted, legati tramite SHA-256 a una queue write-once con
  0 receipt e self-acceptance vietata. Proposal SHA-256
  `73bc241078d7fb32196bdff3adec45932a1cf1f1cf3846721909a27af4aa814f`,
  queue SHA-256
  `c5839d76422e3dd22bcf478a46bb6ca73da9bda32aec2aa15614fa40d9fa27da`
  e audit SHA-256
  `7b9cf376728820c794a9324447eae3e2675c5a3ccd8adb31b516faca6c0d381b`.
  Taxonomy v5 resta byte-identica; scope, acquisizione, foundation, fitting,
  evaluation e outer OOS restano chiusi. Il solo passo autorizzato e' E14.7g,
  handoff e ingestion di receipt indipendenti hash-matching.
  La regressione completa supera 166/166 test Python e 240/240 test .NET.
- Fase E14.7g1 - handoff review esterna: generato un bundle immutabile con
  copia byte-identica della proposta e della queue, 2 dossier verificati, 2
  worksheet e 2 template receipt schema v2 intenzionalmente invalidi finche'
  non compilati da un reviewer indipendente. Audit handoff SHA-256
  `0bf1cbcc51ca8cbf9c7eee7e3bae228a1b0cf1dfad0464b8c6aebf856beb8243`.
  Il validatore E14.7g2 rifiuta hash errati, self-review, receipt duplicate e
  accept privi dei controlli stretti. Il dry-run senza receipt produce stato
  `POST_2005_INDEPENDENT_REVIEW_INCOMPLETE`, queue readiness SHA-256
  `13e13f0d71d58c003c472820524ba33414b4a30713909d3fbdf80d89325078a0`
  e audit SHA-256
  `71a48069d7dc3731f341910bd31f2227c73cf7f16b7913705c79c5234835c120`.
  Nessuna review e' stata simulata sugli artefatti reali: E14.7g resta aperto
  in attesa di due receipt esterne autentiche. La regressione supera 171/171
  test Python e 240/240 test .NET.
- Fasi E14.7g-E14.7l - completate review e remediation, attivato lo scope
  post-2005 separato, preregistrate e acquisite atomicamente sette fonti in 23
  raw artifact. L'audit vintage fail-closed qualifica
  `broad-market-repricing` e `funding-liquidity`, ma blocca `banking-credit` e
  `cross-border-growth` per assenza di release-level vintages H.8/H.10/FDIC.
  La trasformazione globale resta chiusa. La regressione supera 188/188 test
  Python.
- Fase E14.7m - remediation vintage metadata-only: H.8 e' locator-feasible;
  H.10 ha un gap strutturale di 31 mesi e FDIC 2025Q4 e' post-cutoff. Nessuna
  acquisizione e' autorizzata; serve un redesign revisionato di fonte e policy.
- Fase E14.7n - proposta di redesign: G.5 mensile candidato sostitutivo H.10,
  break 2019 esplicito e FDIC vincolato alla pubblicazione corroborata. Due
  dossier hash-bound attendono review indipendente; ogni gate downstream resta
  chiuso.
- Fase E14.7o - gate di handoff bloccato: i due dossier ID E14.7n non possono
  produrre receipt valide sotto lo schema v2 e la struttura di counterevidence
  non coincide. Nessun bundle o template e' stato pubblicato; serve uno schema
  ed evidence contract versionati, senza mutare E14.7n.
- Fase E14.7p - remediation del contratto di review: queue v2, schema receipt
  dedicato ed evidence contract con sette locator, otto finding e due
  counterevidence. I dossier E14.7n restano byte-identici; e' aperto soltanto
  l'handoff immutabile, senza receipt o attivazione.
- Fase E14.7q - handoff immutabile: bundle di 12 file con copie byte-identiche,
  due worksheet e due template hash-bound non ingeribili. Nessuna receipt o
  review e' stata prodotta; il reviewer esterno puo' ora eseguire la review.
- Fase E14.7r - review indipendente e ingestion completate: due receipt
  autentiche accettano entrambi i dossier, con otto finding supportati e due
  counterevidence considerate. La queue v3 e l'audit sono immutabili; solo il
  gate di attivazione policy separato e' autorizzato, mentre tutti i gate dati e
  modello restano chiusi. La regressione supera 222/222 test Python.
- Fase E14.7s - attivato un overlay source-vintage policy v2 senza modificare
  taxonomy o label. G.5 sostituisce H.10 con regimi metodologici separati e
  FDIC usa la pubblicazione effettiva. Il vecchio snapshot non e'
  reinterpretato; e' aperta soltanto la preregistrazione del nuovo manifest e
  request catalog. Acquisizione e gate modello restano chiusi; la regressione
  complessiva supera 229/229 test Python.
- Fase E14.7t - preregistrati manifest e request catalog v2: sette sorgenti,
  H.10 assente, G.5 con 240 mesi unici e FDIC con 79 trimestri eleggibili fino
  al 2025Q3. Gli 11 template sono congelati ma nessuna rete o acquisizione e'
  stata eseguita; resta aperto soltanto il gate metadata separato. La
  regressione complessiva supera 237/237 test Python.
- Fase E14.7u - eseguito il gate metadata fail-closed su manifest/catalog v2.
  Un primo audit immutabile ha bloccato 6/7 sul marker G.5; la remediation v3,
  legata a quel fallimento, ha adottato il campo provider-primary `MonthValue`
  e superato 7/7 probe. Zero template, osservazioni e raw artifact; e'
  autorizzata soltanto l'acquisizione atomica separata. Review indipendente
  approvata e regressione complessiva a 246/246 test Python.
- Fase E14.7v - il preflight discovery-only ha eseguito i tre URL congelati e
  bloccato la full acquisition: H.8 richiede il calendario separato, FDIC
  archivio e prove di pubblicazione, G.5 adjudication per i duplicati 2024-08 e
  2024-10. Staging rimosso, snapshot assente e zero richieste event-time/FRED.
  Review indipendente approvata e regressione a 254/254 test Python.
- Fase E14.7w - preregistrato il docket remediation review-first: H.8 corregge
  1043 a 1042 release, FDIC congela il roster 79/79 ma resta 0/79 sulle date di
  pubblicazione, G.5 conserva originali e correzioni senza backdating.
  Catalogo v3 e snapshot sono assenti; e' aperta soltanto la review
  indipendente. Regressione complessiva a 260/260 test Python.
- Fase E14.7x - review indipendente hash-bound completata con decisione
  `accept`: confermati H.8 1042, roster FDIC 79/79 con gap probatorio ancora
  0/79 e catene G.5 senza retroattivita'. Il docket resta non eseguibile;
  catalogo v3, snapshot v2, rete, acquisizione e downstream restano chiusi.
  Regressione complessiva confermata a 260/260 test Python.
- Fase E14.7y - preregistrata senza rete la raccolta metadata-only delle 79
  prove FDIC: roster esatto 2006Q1-2025Q3, campi provider-primary congelati e
  quarter-end, Last-Modified, lag stimati e fonti secondarie vietati. Il gap
  resta 0/79; l'esecuzione richiede review separata. Catalogo v3 e downstream
  restano chiusi. Regressione complessiva a 266/266 test Python.
- Fase E14.7z - review indipendente del disegno metadata-only completata con
  decisione `accept`: confermati hash, roster 79/79, campi probatori, pinning
  FDIC e guard fail-closed. La review autorizza soltanto un gate di esecuzione
  separato; rete, catalogo v3 e downstream restano chiusi. Suite ancora
  266/266.
- Fase E14.7aa - gate operativo metadata-only superato senza rete: congelati
  host FDIC, budget 158/316, redirect, timeout, limite 8 MiB, content type,
  retry e pubblicazione atomica solo a 79/79. E' autorizzato soltanto il
  collector separato; catalogo v3 e downstream restano chiusi. Regressione
  complessiva a 273/273 test Python.
- Fase E14.7ab - il preflight del collector ha fallito chiuso prima della rete:
  il piano E14.7aa non congela URL seed esatti ne' template hash-bound. Zero
  richieste, righe, raw artifact, ledger e cataloghi pubblicati. La ricognizione
  provider-primary segnala inoltre release storiche su `archive.fdic.gov`, host
  non ammesso dal gate corrente. E' autorizzata soltanto la preregistrazione
  versionata del request catalog e una nuova review del gate. Regressione
  complessiva a 278/278 test Python.
- Fase E14.7ac - preregistrato senza rete il catalogo metadata FDIC: due seed
  esatti, tre template hash-bound e 79 URL trimestrali provider-primary da
  2006Q1 a 2025Q3. `archive.fdic.gov` e' soltanto proposto e tutte le 79 date
  restano irrisolte. E' autorizzata esclusivamente la review indipendente prima
  di un nuovo gate operativo. Regressione complessiva a 283/283 test Python.
- Fase E14.7ad - review indipendente conclusa con `needs_changes`: hash, roster
  79/79, URL, template e zero rete sono confermati, ma il catalogo non congela
  i 79 `ARCHIVE_RECORD_ID` e la discovery archivio conserva discrezionalita' a
  runtime. Il gate sostitutivo resta chiuso; e' ammessa solo una remediation
  hash-bound della mappa quarter-to-archive. Regressione complessiva a 286/286
  test Python.
- Fase E14.7ae - materializzata offline la mappa quarter-to-archive 79/79. Il
  corpus locale non contiene associazioni archivio hash-bound, quindi tutte le
  entry sono esplicitamente irrisolte e la discovery a runtime e' vietata.
  Zero rete e zero record ID inventati; e' autorizzata soltanto la review
  indipendente E14.7af. Regressione complessiva a 291/291 test Python.
- Fase E14.7af - review indipendente conclusa con `needs_changes`: confermati
  hash, roster, URL, zero rete e rimozione della discovery discrezionale, ma
  l'assenza di evidenza locale non dimostra inesistenza dei record FDIC. La
  mappa e' 0/79 risolta; schema mappa e audit richiedono una nuova versione.
  Il gate sostitutivo resta chiuso. Regressione complessiva a 294/294 test
  Python.
- Fase E14.7ag - preregistrato offline il protocollo provider-primary con due
  soli esiti: record archivio esatto con evidenza hash-bound oppure inesistenza
  dimostrata dal provider. Versionati map schema v2 e audit schema v2 chiuso;
  zero rete, request catalog e map v2. E' autorizzata soltanto la review
  indipendente E14.7ah. Regressione complessiva a 299/299 test Python.
- Fase E14.7ah - review indipendente conclusa con `needs_changes`: evidenza non
  legata a URL/request provenance, partizione 79/79 non enforceable tra i due
  esiti, conteggi audit non legati a mappa/manifest e atomicita' solo
  dichiarativa. Discovery catalog ed execution gate restano chiusi. Regressione
  complessiva a 302/302 test Python.
- Fase E14.7ai - versionati evidence manifest URL/request-bound, map schema v3
  a roster singolo, audit schema v3 e validator semantico fail-closed. Il
  validator impone roster 79/79, unicita', outcome/hash provenance e coerenza
  dei conteggi audit. Zero rete e nessun catalogo o map v3; e' autorizzata solo
  la review indipendente E14.7aj. Regressione complessiva a 310/310 test Python.
- Fase E14.7aj - review indipendente conclusa con `needs_changes`: il validator
  accetta file raw inesistenti, request ID duplicati, source catalog inesistente
  e payload schema-invalid; manca inoltre un producer atomico e la copertura
  negativa dei bypass. Discovery catalog ed execution restano chiusi.
  Regressione complessiva a 313/313 test Python.
- Fase E14.7ak - implementati validator integrato e producer atomico fail-closed:
  verifica dei raw bytes, request ID univoci, redirect continui, binding degli
  URL al source catalog e pubblicazione con staging sibling/rename. La matrice
  negativa include confirmed-absent, tampering e rollback senza output parziali.
  Zero rete e zero bundle reali; e' autorizzata soltanto la review indipendente
  E14.7al. Regressione complessiva a 321/321 test Python.
- Fase E14.7al - review indipendente conclusa con `needs_changes`: atomicita'
  locale confermata, ma riprodotti bypass tra source catalog object/raw bytes,
  evidence marker-only e riuso cross-quarter, hash audit non legati ai bytes
  reviewati, raw esterni al bundle e test matrix non execution-derived. Rete,
  discovery ed execution gate restano chiusi; e' ammessa soltanto una nuova
  remediation seguita da review indipendente.
- Fase E14.7am - implementato producer v2 separato: parsing dei bytes
  autenticati, raw/record ID univoci e quarter-bound, absence proof rafforzata,
  gate obbligatorio validato, hash degli esatti bytes reviewati e inclusione dei
  79 raw nel bundle pubblicato con un solo rename. Zero rete e bundle reali;
  e' autorizzata soltanto la review indipendente E14.7an.
- Fase E14.7an - review indipendente conclusa con `needs_changes`: producer v2
  non verifica gli input contro il contratto, accetta schemi gate/catalogo
  caller-controlled e provenance sintetica senza response receipt; mancano
  inoltre revalidation post-write, redirect evidence, confinement ripetuto e
  receipt test hash-bound. Discovery, rete ed execution gate restano chiusi.
- Fase E14.7ao - implementato producer v3 con contract hash trust anchor,
  verifica contrattuale di tutti gli input, response envelope Ed25519 firmati,
  binding request/quarter/URL/redirect/body, confinement ripetuto, revalidation
  post-write e receipt test execution-derived. Zero rete e bundle reali; e'
  autorizzata soltanto la review indipendente E14.7ap.
- Fase E14.7ap - review indipendente conclusa con `needs_changes`: crittografia
  e binding interni confermati, ma il caller controlla contract e trusted hash;
  restano replay cross-run, revalidation incompleta dei JSON staging, receipt
  test non autenticato e finestra check/use. Downstream e rete restano chiusi.
- Fase E14.7aq - implementato producer v4 con registry contract separato,
  envelope anti-replay, collector receipt firmato e attestation mode esplicito,
  descriptor/no-follow reads, revalidation completa dello staging e receipt
  test firmato con transcript. Zero rete e production contract; e' autorizzata
  soltanto la review indipendente E14.7ar.
- Fase E14.7ar - review indipendente conclusa con `needs_changes`: le garanzie
  strutturali v4 sono confermate, ma la chiave del test receipt e' self-trusted,
  la receipt chain e il consumo nonce non sono applicati, la network
  attestation non e' prova indipendente e le hash-map audit sono permissive.
  Discovery, rete, source acquisition ed execution gate restano chiusi.
- Fase E14.7as - implementato producer v5 con signer test esternamente pinned,
  ledger append-only e consumo nonce prima del rename, receipt/bundle schema a
  roster hash chiuso, rifiuto totale della modalita' network e qualifica
  descriptor-identity Windows. Zero rete e production contract; e' autorizzata
  soltanto la review indipendente E14.7at.
- Fase E14.7at - review indipendente conclusa con `needs_changes`: cross-parent
  replay riprodotto perche' il ledger deriva dal target, rollback/cancellazione
  del ledger non sono ancorati esternamente, crash recovery e stale-lock
  recovery sono incomplete. Trust runner, blocco rete e schemi sono confermati;
  discovery, rete ed execution gate restano chiusi.
- Fase E14.7au - implementato state layer producer v6 con root code-pinned,
  anchor monotono separato, detection di deletion/rollback, recovery
  pending/committed e stale-lock owner-aware. Zero rete e production contract;
  e' autorizzata soltanto la review indipendente E14.7av.
- Fase E14.7av - review indipendente conclusa con `needs_changes`: root
  copiabile, rollback coordinato ledger-anchor, crash post-rename, target
  cross-volume, marker unsigned/symlink, directory durability e PID reuse
  restano aperti. Rete e downstream restano chiusi.
- Fase E14.7aw - introdotto boundary v7 fail-closed per authority monotona
  esterna; registry production vuoto, self-pin e fallback locale respinti,
  zero provisioning, target e rete. E' autorizzata soltanto E14.7ax review.
- Fase E14.7ax - review indipendente `accept`: E14.7 chiusa come `safely
  blocked`. Nessuna capacita' di pubblicazione, provisioning, rete o downstream;
  un authority adapter futuro richiede autorizzazione e review separate.
- Fase E14.8 - preregistrato il provisioning dell'authority esterna in modalita'
  design-only e provider-neutral: 18 capacita' e 10 evidenze obbligatorie,
  zero rete, risorse, credenziali o runtime mutation. Aperta soltanto E14.8a.
- Fasi E14.8a-E14.8c - la prima review ha richiesto roster non omissibile e
  protocollo operativo; E14.8b ha congelato state machine, CAS, recovery e 14
  test futuri, quindi E14.8c ha accettato e chiuso E14.8 safely blocked.
- Consolidamento E14.7-E14.8 - inventariati e verificati checkpoint 0122-0145,
  contratti, modelli ed evidenze; 240 test C# e 413 test Python verdi. Gli hash
  aggregati fissano il payload versionabile e le 32 evidenze locali, mentre
  provider, rete, pubblicazione e downstream restano chiusi. Dettaglio nel
  checkpoint `docs/checkpoints/0146-consolidamento-e14-7-e14-8.md`.

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
input. Nel frattempo e' stato completato il consolidamento Git degli artefatti
runtime `.tmp`. La baseline v1.4 resta congelata e lo scoring anticipato resta
vietato.

## Riorganizzazione documentale (2026-07-09)

Tutti i documenti markdown sono stati spostati in `docs/`, organizzati per categoria e rinominati con progressivo temporale:

- `docs/research/`: documenti di ricerca (0001-0002);
- `docs/planning/`: piani, governance, post-mortem e restart (0001-0007);
- `docs/adr/`: decisioni architetturali (0001-0004);
- `docs/domain/`: glossario, mapping e design del dominio (0001-0003);
- `docs/testing/`: test plan (0001);
- `docs/checkpoints/`: chiusure e audit degli step implementativi (0001-0026).
