# Macro-Regime Engine - Piano operativo completo

Data: 2026-07-13

## Scopo

Questo documento consolida in un unico punto l'intero piano operativo del progetto Macro-Regime Engine: la visione, le regole non negoziabili, le fasi gia' chiuse e la sequenza di lavoro da seguire da qui in avanti.

I documenti di dettaglio restano la fonte autorevole:

- visione e architettura funzionale: `docs/planning/0001-piano-macro-regime-engine.md`;
- governance: `docs/planning/0003-governance-progetto.md`;
- delivery plan e milestone: `docs/planning/0004-delivery-plan.md`;
- restart architetturale: `docs/planning/0007-piano-restart-architetturale.md`;
- stato di avanzamento: `docs/0002-riepilogo-lavoro-svolto.md`.



## Obiettivo del progetto

Costruire un Macro-Regime Engine professionale a supporto della strategia di portafoglio personale: non un singolo modello predittivo, ma una pipeline governata, auditabile ed estendibile che separa dati, feature, classificazione del regime, proposta allocativa, controlli di rischio e decisione umana.

## Principi non negoziabili

- Il regime e' probabilistico, non una singola etichetta deterministica.
- Lo stato `UncertainTransition` e' obbligatorio quando i segnali divergono.
- Ogni calcolo deve essere ricostruibile as-of date, con fonte, osservazione, pubblicazione e versione del modello.
- Le decisioni allocative sono subordinate a IPS, bande strategiche, turnover, costi e fiscalita'.
- La baseline rule-based precede sempre i modelli avanzati; HMM, clustering e jump model entrano come challenger, non come motore primario.
- `MacroRegime.Domain` non contiene riferimenti a EF Core, ASP.NET, HTTP, database, file system o clock di sistema.
- Ogni promozione di modello richiede Model Gate; la decisione finale resta umana.



## Architettura di riferimento

```text
MacroRegime.slnx
src/
  MacroRegime.Domain/          dominio puro, nessuna dipendenza esterna
  MacroRegime.Application/     use case e porte, dipende solo da Domain
  MacroRegime.Infrastructure/  adapter: import JSON, run store, manifest
  MacroRegime.Reporting/       renderer markdown dei report
  MacroRegime.Cli/             esecuzione end-to-end locale
  MacroRegime.Web/             dashboard read-only
tests/                         un progetto test per layer
research/regime-eval/          research lab Python isolato dal runtime
docs/                          documentazione organizzata per categoria
```

Le regole di dipendenza complete sono in `docs/adr/0002-dipendenze-layer.md`.

## Fasi completate (sintesi)

1. Ricerca e impostazione: stato dell'arte, analisi progetti GitHub, piano, governance, delivery plan.
2. Post-mortem del primo tentativo (prototipo Finance) e decisione di restart architetturale.
3. Baseline documentale: ADR 0001/0002, glossario, prototype mapping, domain core design, test plan.
4. Step 1-14 di implementazione: domain core, baseline rule-based detector, allocation proposal vincolata, vertical slice, adapter demo, import dati/config JSON locali, CLI, Web UI read-only, run manifest.
5. Prima release informativa chiusa il 2026-07-08: build verde, 126 test superati, run riproducibile end-to-end.
6. Fase A (consolidamento storico e confronto run) chiusa il 2026-07-09: run JSON v2 con allocation e data source, dettaglio storico letto da disco senza riesecuzione, pagina di confronto tra run, test Web dedicati; 141 test superati.
7. Fase B (import dati e diagnostica) chiusa il 2026-07-09: report diagnostico import/config, CLI `--validate-only`, batch multi-data, pagina Web `/ImportDiagnostics`; 150 test superati.
8. Fase C (decisione persistenza) chiusa il 2026-07-10: persistenza locale file-based formalizzata come scelta stabile per ora; database rimandato a trigger espliciti e nuova ADR.
9. Fase D - Slice 1 (adapter FRED isolato con stub) chiusa il 2026-07-10: porta `IExternalMacroDataSource`, use case `DownloadMacroDataUseCase`, stub deterministico `FredStubMacroDataSource`, writer `JsonMacroDataFileWriter`, CLI `--download-fred` offline; ADR 0004 sull'isolamento di rete; 172 test superati.
10. Fase D - Slice 2 (client HTTP FRED reale) chiusa il 2026-07-10: adapter `FredHttpMacroDataSource` in Infrastructure, API key da `--fred-api-key`/`FRED_API_KEY`, retry su errori transitori, CLI `--fred-source stub|http`; runtime core ancora senza rete.
11. Fase D - Slice 3 (vintage reale e calendario release) chiusa il 2026-07-10: il downloader HTTP seleziona il vintage reale via `fred/series/vintagedates`; nuovo `FredReleaseCalendarClient` per `releases/dates` e `release/dates`; baseline FRED corretto usando `INDPRO` trasformato in `INDPRO_YOY`; rete ancora confinata in Infrastructure.
12. Fase D - Slice 4 (provider market data esterno) chiusa il 2026-07-10: porta e use case market data, stub deterministico, writer JSON `market-data-{asOf}.json`, adapter Yahoo Finance chart endpoint isolato in Infrastructure; provider utile per uso personale/ricerca ma trattato come non ufficiale e sostituibile.
13. Fase D - Slice 5 (dataset storico macro+market) chiusa il 2026-07-10: builder locale `HistoricalDatasetBuilder`, comando CLI `--build-historical-dataset`, merge di file macro/market locali e forward returns su orizzonti configurabili.
14. Fase E - Slice 1 (research data gate) chiusa il 2026-07-13: creato `research/regime-eval/`, protocollo anti-leakage, validatore del dataset storico, manifest riproducibile SHA-256 e planner walk-forward rolling 10/2/1; 6 test Python superati.
15. Fase E - Slice 2 (dataset reale pluriennale) chiusa il 2026-07-13: popolatore bulk FRED/ALFRED e Yahoo, corpus mensile 2008-2025, manifest del corpus e del dataset, 213 righe validate e 6 fold walk-forward completi.
16. Fase E - Slice 3 (baseline walk-forward) chiusa il 2026-07-13: evaluator C# della baseline autorevole, report Python deterministico sui sei fold, metriche di confidenza/stabilita' e rendimenti forward condizionati; nessuna accuracy senza ground truth versionata.
17. Fase E - Slice 4 (ground truth NBER) chiusa il 2026-07-13: cronologia recessiva mensile versionata con fonti e hash, report confusion-matrix per primary/operational `DeflationBust`, date di errore e detection lag; limiti ex-post e class imbalance espliciti.
18. Fase E - Slice 5 (primo challenger clustering) chiusa il 2026-07-13: k-means deterministico train-only, configurazione congelata, test anti-leakage, report comparativo e model card; risultato negativo conservato e modello non promosso.
19. Fase E - Slice 6 (feature e baseline redesign) chiusa il 2026-07-13: baseline v1.4 supera train gate v2 e audit OOS; resta baseline di ricerca, non promozione operativa.
20. Fase E - Slice 7 (challenger temporale) chiusa il 2026-07-13: Gaussian HMM v1 causale e train-only valutato e respinto per regressione di recall e F1.
21. Fase E - Slice 8 (evaluation contracts e shadow ledger) chiusa il 2026-07-13: prediction, scoring e decisione umana separati in artefatti immutabili; dry-run completato, shadow-live reale ancora da avviare.
22. Fase E - Slice 8, primo incremento operativo chiuso il 2026-07-13: prima
    previsione shadow-live al cutoff 2026-06-30 congelata senza outcome; un dato
    SAHM obsoleto e' stato intercettato e corretto prima del ledger.
23. Fase E - stress non recessivi v1 chiuso il 2026-07-13: cronologia multi-label
    versionata, anti-overlap NBER e report v1.4; risultato negativo conservato,
    con blind spot sugli stress finanziari e nessun tuning post-hoc.
24. Fase E9 - Shadow Operations, primo incremento chiuso il 2026-07-13:
    preflight immutabile, gate su mese chiuso/freshness/assenza label,
    fingerprint C#/Python, retry idempotente e indice derivato dei ledger.
25. Fase E9 - Shadow Operations, secondo incremento implementato il 2026-07-14:
    orchestratore mensile, layout standard, `prepare-only/full`, stato
    recuperabile, log/hash dei processi C# e recovery dai fallimenti parziali.

Il dettaglio per ogni step e' in `docs/checkpoints/` (progressivi 0001-0045).

## Piano operativo da seguire

La direzione decisa alla chiusura della prima release e': prima rendere il sistema informativo piu' affidabile nel tempo, poi renderlo piu' sofisticato.

### Fase A - Consolidamento storico e confronto run (COMPLETATA, 2026-07-09)

1. Lettura del dettaglio di una run storica direttamente dal run JSON salvato, senza riesecuzione della pipeline. Fatto: pagina `/RunDetail` e `LoadRegimeRunUseCase`.
2. Confronto tra due run (regime, probabilita', feature, proposta) in report e/o UI. Fatto: pagina `/CompareRuns` e `CompareRegimeRunsUseCase`.
3. Test Web dedicati (progetto test Web o smoke automatizzato) per superare la verifica solo manuale/HTTP. Fatto: `MacroRegime.Web.Tests` con `WebApplicationFactory`.

Checkpoint: `docs/checkpoints/0021-fase-a-storico-confronto-run-done.md`.



### Fase B - Import dati e diagnostica (COMPLETATA, 2026-07-09)

1. Report di validazione import/config separato e leggibile. Fatto: `ValidateImportCommand`, `IImportValidationService`, `JsonImportValidationService`, renderer markdown, CLI `--validate-only`.
2. Estensione dei dataset locali oltre i sample demo, verso serie macro storiche reali. Fatto: convenzione locale per file datati `macro-data-yyyy-MM-dd.json` e `current-portfolio-yyyy-MM-dd.json`; resta fuori il dataset reale ampio.
3. Import storico esteso multi-data per popolare il manifest con piu' as-of date. Fatto: CLI batch con `--batch-from`, `--batch-to`, `--data-dir`, `--portfolio-dir`.

Checkpoint: `docs/checkpoints/0022-fase-b-import-diagnostica-done.md`.



### Fase C - Decisione persistenza (COMPLETATA, 2026-07-10)

1. Valutare se e quando introdurre un database locale (ADR dedicata). Fatto: ADR 0003.
2. In caso positivo, introdurre la persistenza solo come adapter in Infrastructure, senza toccare Domain e Application. Fatto: non introdotto ora.
3. In caso negativo, formalizzare il file-based come scelta di lungo periodo. Fatto: file-based confermato come persistenza locale stabile per la prossima fase.

Checkpoint: `docs/checkpoints/0023-fase-c-decisione-persistenza-done.md`.

ADR: `docs/adr/0003-persistenza-locale-file-based.md`.



### Fase D - Provider dati esterni

1. Adapter FRED/ALFRED dietro le porte applicative esistenti. Slice 1 fatta: porta `IExternalMacroDataSource`, stub `FredStubMacroDataSource`, CLI `--download-fred`; Slice 2 fatta: client HTTP reale `FredHttpMacroDataSource` in Infrastructure e selezione CLI `--fred-source stub|http`.
2. Gestione vintage reale e calendario rilasci. Slice 3 fatta: `series/vintagedates` per selezione vintage point-in-time e `FredReleaseCalendarClient` per calendario release.
3. Provider market data esterno. Slice 4 fatta: porta `IExternalMarketDataSource`, stub deterministico, writer JSON `JsonMarketDataFileWriter`, CLI `--download-market-data`, adapter Yahoo isolato.
4. Dataset storico macro+market. Slice 5 fatta: builder file-based, comando CLI `--build-historical-dataset`, forward returns 28/56/91 giorni configurabili, output `historical-dataset-{from}-{to}.json`.
5. Nessuna rete nel runtime core: il download resta un adapter isolato. Fatto: ADR 0004, gate verificato (nessun `HttpClient` in Domain/Application/Web).

Checkpoint Slice 1: `docs/checkpoints/0024-fase-d-slice1-adapter-fred-stub-done.md`.

Checkpoint Slice 2: `docs/checkpoints/0025-fase-d-slice2-fred-http-done.md`.

Checkpoint Slice 3: `docs/checkpoints/0026-fase-d-slice3-vintage-calendar-done.md`.

Checkpoint Slice 4: `docs/checkpoints/0027-fase-d-slice4-market-data-yahoo-done.md`.

Checkpoint Slice 5 / chiusura Fase D: `docs/checkpoints/0028-fase-d-complete-dataset-storico-done.md`.

ADR: `docs/adr/0004-isolamento-rete-adapter-fred.md`.

La Fase D e' completa per il perimetro dati esterni: adapter macro FRED/ALFRED, adapter market data, file JSON locali, dataset storico macro+market e forward returns. Restano futuri ma non bloccanti per Fase E: UI/persistenza calendario release, dataset reale ampio popolato su molti anni e indici/controlli file-based piu' evoluti.



### Fase E - Research lab e modelli challenger (IN CORSO, 2026-07-13)

1. Creare `research/regime-eval/` con protocollo di valutazione (Python; il runtime resta C#). Fatto nella Slice 1: laboratorio standard-library, protocollo, CLI e test isolati.
2. Walk-forward obbligatorio: train 10 anni, test 2 anni, avanzamento 1 anno; nessuna selezione iperparametri sul test. Fatto nella Slice 1 per la pianificazione rolling e il gate di copertura; esecuzione dei modelli ancora da implementare.
   Gate di copertura superato nella Slice 2: dataset reale 2008-2025 con 6 fold completi; l'esecuzione dei modelli resta da implementare.
   Baseline eseguita nella Slice 3: 213 predizioni e report sui 6 fold; essendo il modello corrente efficace dal 2026, il risultato e' un benchmark retrospettivo e non una performance live ex-ante.
3. Challenger: HMM, Markov switching, clustering, jump model; sempre confrontati con la baseline rule-based.
   Primo challenger completato nella Slice 5: clustering k-means v1 non promosso per recall OOS nullo; configurazione, report e model card conservati.
4. Metriche composite: regime accuracy vs NBER, asset alignment 4-13 settimane, tilt simulation, penalita' asimmetrica sui falsi negativi in Stagflazione e Deflation/Bust.
5. Promozione di un challenger solo tramite Model Gate con model card.

6. Slice E6 - Feature and Baseline Redesign (COMPLETATA, 2026-07-13). La revisione
   dopo E5 ha rilevato saturazione delle feature, concentrazione quasi totale su
   `Goldilocks` e insufficienza degli episodi recessivi OOS. Prima di introdurre
   HMM o altri challenger temporali, E6 deve:
   - rendere automatico e versionato l'audit di saturazione, diversita' dei
     regimi e copertura operativa;
   - verificare la raggiungibilita' dei cinque regimi primari con scenari
     macroeconomici archetipici;
   - ridisegnare credito, condizioni monetarie e inflazione evitando proxy con
     scale incompatibili e trasformazioni monotone ambigue;
   - produrre una baseline v1 separata dalla `0.1-demo`, rieseguire walk-forward
     e ground truth e documentare esplicitamente ogni regressione;
   - separare, nelle slice successive, lo storico macro di classificazione dallo
     storico market usato per i forward return e riservare un holdout fresco o
     uno shadow-live 2026+.

   L'HMM e' sospeso fino al superamento dei gate E6. Il benchmark 2008-2025,
   gia' osservato durante E3-E6, resta development/validation e non deve essere
   presentato come test finale incontaminato.

   Secondo incremento eseguito il 2026-07-13: pubblicata la research candidate
   `1.0-candidate`, separata dalla demo e selezionabile nella sola valutazione
   storica. La saturazione credito e la diversita' migliorano, ma il gate resta
   negativo per concentrazione Goldilocks e quota di incertezza. La candidate
   non e' promossa e la soglia non viene ritoccata sul benchmark osservato.

   Terzo incremento eseguito il 2026-07-13: creato un corpus separato con CPI YoY
   point-in-time, momentum CPI e variazione trimestrale della curva. La candidate
   `1.1-candidate` supera saturazione, diversita' e concentrazione, ma resta non
   promossa per `UncertainTransition` al 75%. Il prossimo incremento E6 riguarda
   raw score/confidence con configurazione preregistrata e stima train-only.

   Quarto incremento eseguito il 2026-07-13: introdotta la `1.2-candidate` con
   scoring archetipico e confidence fit/margine, piu' un gate train-only
   riproducibile. Il preflight ha prodotto 0 fold eleggibili su 6 e ha bloccato
   l'apertura dei report OOS. Il prossimo incremento E6 deve preregistrare un gate
   v2 che valuti integrita' feature e copertura su validation aggregate, lasciando
   per-fold i controlli di robustezza operativa; solo dopo potra' nascere una v1.3.

   Quinto incremento eseguito il 2026-07-13: il train gate v2 e' stato
   preregistrato e implementato mantenendo le soglie v1. Copertura aggregata e
   robustezza operativa passano, mentre l'integrita' fallisce per
   `RISK_APPETITE` al 27,38% di boundary rate contro il 25%. La v1.2 resta
   bloccata; il prossimo incremento e' una v1.3 con normalizzazione VIX
   ridisegnata e nuova preregistrazione train-only.

   Sesto incremento eseguito il 2026-07-13: la `1.3-candidate` sostituisce solo
   il mapping VIX con una logistica inversa preregistrata. L'integrita' passa e
   `RISK_APPETITE` scende all'1,19% di boundary rate; copertura ancora superata.
   La robustezza operativa regredisce pero' a 2/6 fold e blocca l'OOS. Il prossimo
   incremento deve riallineare archetipi e confidence alla scala delle feature
   usando esclusivamente inner fit/validation e pubblicando una nuova versione.

   Settimo incremento eseguito il 2026-07-13: la `1.4-candidate` riallinea
   semanticamente archetipi, cutoff divergente e confidence alla scala VIX
   logistica. Il train gate passa 6/6 fold e autorizza l'OOS, che supera l'audit
   con zero violazioni, 4 regimi e 2,38% di incertezza. NBER conserva recall 100%
   ma precision 20% e F1 33,33%. E6 e' chiusa; v1.4 e' baseline di ricerca, non
   modello operativo promosso. Il prossimo passo e' un challenger temporale
   contro v1.4 e uno shadow-live 2026+.

Gate dati introdotto nella Slice 1:

- validazione schema e coerenza dei forward returns;
- controlli point-in-time su observation/publication/availability date;
- manifest con hash, dimensione, copertura, simboli e orizzonti;
- nessun fold completo se il dataset copre meno di 12 anni;
- sample demo esclusi da qualunque Model Gate.

La Slice 2 ha popolato e manifestato il dataset reale pluriennale: 213 snapshot macro mensili, 4.536 snapshot market giornalieri, 3.834 forward return e 6 fold rolling. Il corpus locale e' sotto `data/historical-real-2008-2025/` ed e' escluso da Git; gli artefatti sono identificati da SHA-256.

E6-E8 sono completate e il Gaussian HMM v1 e' stato valutato e respinto. La
prima osservazione realmente shadow-live, con cutoff 2026-06-30, e' stata
congelata senza outcome. La priorita' corrente e' accumulare i successivi ledger
mensili immutabili. La cronologia stress v1 e' ora disponibile e ha rilevato un
blind spot; un eventuale contratto v2 dovra' essere dimensionale e validato su
episodi nuovi, senza selezionare varianti sul benchmark gia' osservato.
Restano inoltre pianificati: indice operativo incrementale per corpus grandi,
integrazione persistita del calendario release e stress test successivi.

Checkpoint Slice 1: `docs/checkpoints/0029-fase-e-slice1-research-data-gate-done.md`.

Checkpoint Slice 2: `docs/checkpoints/0030-fase-e-slice2-dataset-reale-pluriennale-done.md`.

Checkpoint Slice 3: `docs/checkpoints/0031-fase-e-slice3-baseline-walk-forward-done.md`.

Checkpoint Slice 4: `docs/checkpoints/0032-fase-e-slice4-ground-truth-nber-done.md`.

Checkpoint Slice 5: `docs/checkpoints/0033-fase-e-slice5-primo-challenger-clustering-done.md`.

Checkpoint Slice 6: completata; avvio e primo audit sono documentati in
`docs/checkpoints/0034-fase-e-slice6-feature-baseline-redesign-in-progress.md`,
chiusura in `docs/checkpoints/0038-fase-e-slice6-v14-gates-passed-done.md`.

Checkpoint v1.2 train gate:
`docs/checkpoints/0035-fase-e-slice6-v12-train-gate-rejected.md`.

Checkpoint train gate v2:
`docs/checkpoints/0036-fase-e-slice6-train-gate-v2-done.md`.

Checkpoint v1.3:
`docs/checkpoints/0037-fase-e-slice6-v13-vix-train-gate-rejected.md`.

Checkpoint chiusura E6 / v1.4:
`docs/checkpoints/0038-fase-e-slice6-v14-gates-passed-done.md`.

7. Slice E7 - Challenger temporale Gaussian HMM (COMPLETATA, 2026-07-13).
   Il modello v1 a tre stati e' stato preregistrato contro la baseline v1.4,
   implementato con Baum-Welch deterministico e inferenza test causale, quindi
   eseguito sui 6 fold. Tutti i fit convergono, ma il gate fallisce: recall 50%
   e F1 11,76% contro 100% e 33,33% della baseline. Il challenger e' respinto
   senza tuning post-hoc. La priorita' successiva diventa predisporre lo
   shadow-live 2026+ e una ground truth degli stress non recessivi prima di
   aprire altre varianti temporali sul benchmark gia' osservato.

Checkpoint Slice 7:
`docs/checkpoints/0039-fase-e-slice7-gaussian-hmm-v1-rejected.md`.

8. Slice E8 - Evaluation Contracts & Shadow Ledger (COMPLETATA, 2026-07-13).
   Prima dello shadow-live sono stati separati formalmente prediction ledger,
   scoring successivo e decisione umana del Model Gate. Ogni artefatto e'
   immutabile, lega il precedente tramite SHA-256 e registra model lifecycle,
   input, fingerprint del codice e runtime. Il ledger conserva probabilita'
   recessiva e distribuzione completa dei regimi senza includere outcome. Le
   metriche binarie sono ora condivise dai challenger. Un dry-run reale sui mesi
   febbraio-maggio 2020 ha verificato il flusso senza essere qualificato come
   shadow-live o nuovo benchmark.

Checkpoint Slice 8:
`docs/checkpoints/0040-fase-e-slice8-evaluation-contracts-shadow-ledger-done.md`.

Checkpoint prima osservazione shadow-live:
`docs/checkpoints/0041-fase-e-slice8-prima-osservazione-shadow-live-done.md`.

Checkpoint stress non recessivi v1:
`docs/checkpoints/0042-fase-e-stress-non-recessivi-v1-done.md`.

9. Fase E9 - Shadow Operations (IN CORSO, 2026-07-13).
   Obiettivo: rendere operativo il protocollo E8 mantenendo separati download,
   preparazione, previsione e scoring. E9 non autorizza tuning del modello.

   Primo incremento (COMPLETATO, 2026-07-13):

   - `ShadowPreflight` immutabile, legato tramite hash a dataset, evaluation e
     model config;
   - cutoff ammesso solo dopo la chiusura del mese informativo;
   - nessun forward return nel dataset shadow e freshness massima di tre mesi
     per le serie macro richieste;
   - fingerprint deterministico delle sorgenti C# che producono dati/evaluation
     e del research lab Python;
   - creazione idempotente del ledger: una retry con gli stessi input restituisce
     l'artefatto esistente, mentre un conflitto viene bloccato;
   - `ShadowIndex` deterministico e ricostruibile dai ledger, mai fonte
     autorevole e mai contenitore di outcome.

   Esecuzione reale di verifica:

   - creato un `ShadowPreflight` retrospettivo sul cutoff 2026-06-30;
   - verificati nove segnali macro, tutti entro un mese di lag;
   - il preflight retrospettivo non e' stato collegato al ledger gia' congelato,
     che conserva lo stesso SHA-256;
   - costruito il primo `ShadowIndex` derivato con una sola entry;
   - aggiunti i comandi `shadow-preflight`, `shadow-cycle` e `shadow-index`;
   - 22 test Python superati, inclusi mese aperto, staleness, retry identica e
     conflitto con artefatto immutabile.

   Secondo incremento (IMPLEMENTATO, 2026-07-14):

   - comando `shadow-operations` che determina il prossimo cutoff senza saltare
     mesi e orchestra i processi C# di population, dataset build ed evaluation;
   - modalita' `prepare-only`, che si ferma al preflight, e `full`, che congela
     ledger e indice solo dopo tutti i gate;
   - layout `cycles/yyyy-MM/{source,dataset,evaluation,preflight,logs}` e stato
     atomico `cycle-state.json`;
   - comando, exit code, timestamp e SHA-256 di stdout/stderr e artefatti per
     ogni tentativo, senza API key nella command line;
   - retry che valida e salta gli step completati, riprendendo dal primo step
     fallito senza sovrascrivere ledger;
   - receipt immutabile `ShadowOperationsRun`, sempre senza outcome;
   - smoke reale al 2026-07-14: `no-eligible-month`, zero comandi eseguiti e
     nessun secondo ledger di giugno.

   Attivazione prospettica ancora da eseguire: il primo cutoff nuovo possibile
   e' 2026-07-31, non prima della chiusura del mese e della disponibilita' degli
   input. E9 resta in corso fino a quel primo ciclo `full` reale senza scoring.

   Gate E9: nessuna sovrascrittura dei ledger, nessuna label nel ciclo di
   previsione, indice interamente derivabile, rete confinata in Infrastructure e
   nessuna dipendenza Python nel runtime C#.

   Checkpoint primo incremento:
   `docs/checkpoints/0043-fase-e9-shadow-operations-incremento1-done.md`.

   Checkpoint secondo incremento:
   `docs/checkpoints/0044-fase-e9-shadow-operations-incremento2-done.md`.

   Consolidamento repository (COMPLETATO, 2026-07-14):

   - esclusi globalmente dal tracciamento Git gli artefatti runtime `.tmp`;
   - rimossi dall'indice, ma conservati localmente, output di smoke, batch,
     report e chiavi ASP.NET Core Data Protection generate in sviluppo;
   - nessuna riscrittura della cronologia: l'eventuale purge dei commit storici
     resta un intervento separato, distruttivo e soggetto ad autorizzazione.

   Checkpoint consolidamento:
   `docs/checkpoints/0045-git-hygiene-runtime-artifacts-done.md`.



### Fase F - Ottimizzazione vincolata e stress test

1. Ottimizzazione allocativa vincolata: bande IPS, turnover massimo, costi, fiscalita', penalita' per portafogli estremi, shrinkage sugli expected return.
2. Stress test storici: 1973-74, 2000-02, 2008-09, 2020, 2022.
3. Stress fattoriali: tassi +300bp, HY spread +500bp, USD +20%, equity -35%, correlazioni a 1.
4. Reverse stress test sul rischio primario: liquidazione forzata in momento avverso.



## Regole di esecuzione per ogni fase

- Ogni step si chiude con un checkpoint in `docs/checkpoints/` (progressivo successivo).
- Ogni step deve lasciare build e test verdi; gli step con impatto architetturale richiedono verifica dei gate (nessuna dipendenza vietata nei layer core).
- Le deviazioni dal piano vanno motivate per iscritto nel checkpoint.
- Fermarsi a riepilogare risultato e rischi alla fine di ogni fase prima di passare alla successiva, salvo richiesta esplicita di continuare.



## Fuori scope permanente

- Esecuzione ordini e trading automatico.
- Raccomandazioni non vincolate da policy.
- Decisione allocativa automatica senza approvazione umana.
