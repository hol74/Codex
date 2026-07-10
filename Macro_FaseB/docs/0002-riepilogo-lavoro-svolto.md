# Macro-Regime Engine - Riepilogo del lavoro svolto

Data: 2026-07-09

## Scopo

Questo documento riassume in ordine cronologico tutto il lavoro svolto sul progetto Macro-Regime Engine, dalla ricerca iniziale alla chiusura della prima release informativa (2026-07-08), alla Fase A di consolidamento e alla Fase B su import dati e diagnostica (2026-07-09). Il dettaglio di ogni passaggio e' nei documenti citati.

## Stato attuale in una frase

La prima release informativa e' completa e consolidata dalle Fasi A e B: il sistema calcola una baseline rule-based, produce probabilita' di regime con driver e segnali contrari, genera una proposta allocativa vincolata, salva run complete (regime + allocation + data source) in JSON file-based, indicizza lo storico locale, permette di consultare e confrontare le run salvate senza rieseguire la pipeline, valida import/config con report markdown, supporta batch multi-data locale ed e' consultabile via CLI e Web UI read-only coperta da test. Build verde, 150 test superati, nessun database, nessuna rete runtime.

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

## Verifiche allo stato attuale (dopo Fase B)

- `dotnet build MacroRegime.slnx`: build superata, 0 warning, 0 errori.
- `dotnet test MacroRegime.slnx`: 150 test superati, 0 falliti (Domain 79, Application 24, Infrastructure 32, Reporting 2, CLI 7, Web 6).
- Smoke CLI validate-only: report markdown generato con `OK: 6` e `Errors: 0`.
- Smoke CLI batch: due run generate per `2026-07-01` e `2026-07-02`, manifest popolato.
- Smoke Web: `/ImportDiagnostics?asOfDate=2026-07-01` risponde 200 e mostra `Import Validation Report`, `Macro data`, `Current portfolio`, `OK:`.
- Gate architetturali rispettati: nessuna dipendenza vietata nei layer core, nessun database, nessuna rete runtime.

## Deviazione documentata dal piano originario

Il piano originario prevedeva una prima persistenza anche in chiave EF Core. Dopo il restart e' stata scelta consapevolmente una prima release file-based, senza database, per proteggere dominio, testabilita', as-of semantics e audit trail. La scelta e' intenzionale e tracciata nei checkpoint.

## Cosa resta fuori (non ancora fatto)

- Database ed EF Core.
- Provider dati esterni FRED/ALFRED.
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

I prossimi passi sono definiti nel piano operativo consolidato: `docs/0001-piano-operativo.md`. Le Fasi A e B sono completate; la prossima e' la Fase C (decisione sulla persistenza locale e ADR dedicata).

## Riorganizzazione documentale (2026-07-09)

Tutti i documenti markdown sono stati spostati in `docs/`, organizzati per categoria e rinominati con progressivo temporale:

- `docs/research/`: documenti di ricerca (0001-0002);
- `docs/planning/`: piani, governance, post-mortem e restart (0001-0007);
- `docs/adr/`: decisioni architetturali (0001-0002, gia' presenti);
- `docs/domain/`: glossario, mapping e design del dominio (0001-0003);
- `docs/testing/`: test plan (0001);
- `docs/checkpoints/`: chiusure e audit degli step implementativi (0001-0022).
