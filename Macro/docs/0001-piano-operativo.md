# Macro-Regime Engine - Piano operativo completo

Data: 2026-07-14

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
26. Fase E14.7f chiusa il 2026-07-16: proposta taxonomy post-2005 con nuovi
    identificatori, due dossier banking hash-bound e queue write-once per
    review indipendente; scope, dati e modellazione restano chiusi.
27. Fasi E14.7g-E14.7l chiuse il 2026-07-16: review indipendente e remediation,
    attivazione scope separato, preregistrazione e acquisizione raw atomica,
    quindi audit vintage. Passano 2 famiglie su 4; H.8/H.10/FDIC richiedono
    artifact datati di release e la trasformazione resta chiusa.

Il dettaglio per ogni step e' in `docs/checkpoints/` (progressivi 0001-0105).

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

   Release tecnica E9.2 (COMPLETATA, 2026-07-14):

   - CI GitHub per build/test .NET e laboratorio Python;
   - release notes versionate;
   - integrazione fast-forward in `main` e tag annotato
     `macro-regime-e9.2`;
   - nessuna modifica alla baseline o apertura anticipata del cutoff luglio.

   Checkpoint release:
   `docs/checkpoints/0046-release-e9-2-ci-done.md`.



### Fase E10 - Model Evidence v2 e challenger dual-timescale (COMPLETATA, 2026-07-14)

E10 trasforma i risultati della baseline v1.4 e dei challenger respinti in un
nuovo ciclo di ricerca senza riaprire il tuning sul benchmark 2008-2025.

1. Congelare gli stati esistenti: v1.4 resta `research-baseline`; k-means v1 e
   Gaussian HMM v1 restano `rejected`. Nessun artefatto precedente viene
   sovrascritto.
2. Introdurre un Evidence & Promotion Contract v2 con lifecycle distinti
   (`research-baseline`, `shadow-candidate`, `operational-candidate`,
   `operational-approved`), esito `INSUFFICIENT_EVIDENCE`, metriche
   probabilistiche, precision-recall, calibrazione ed errori per episodio.
3. Versionare uno stress contract v2 dimensionale: crescita, inflazione, stress
   finanziario e restrizione monetaria sono valutati separatamente prima della
   composizione in un regime. La cronologia v1 resta congelata.
4. Preregistrare `dual-timescale-regime-v1`, con componente macro lenta e
   componente finanziaria rapida, filtro esclusivamente causale e output
   probabilistico dimensionale. Il modello ha nuovo id e nuova model card; non
   e' una variante post-hoc dei challenger respinti.
5. Eseguire il nuovo challenger sul 2008-2025 esclusivamente come diagnostica di
   sviluppo. Il benchmark gia' osservato non puo' produrre promozione.
6. Usare inner rolling validation per ogni scelta futura e riservare la
   decisione operativa ai ledger shadow-live prodotti dopo la preregistrazione.
7. Eseguire il primo ciclo E9 `full` sul cutoff 2026-07-31 solo dopo la chiusura
   del mese e la disponibilita' point-in-time degli input. Fino ad allora lo
   step e' temporalmente bloccato, non fallito.
8. Ammettere una promozione solo dopo evidenza prospettica sufficiente, utilita'
   allocativa della Fase F e decisione umana persistita. La mera convergenza o
   il miglioramento sul benchmark storico non sono sufficienti.

Ogni incremento E10 produce configurazione preregistrata, test, report e model
card/checkpoint. I report storici devono riportare esplicitamente
`development-diagnostic-only` e non possono generare una decisione
`operational-approved`.

Esito: Evidence v2 conferma `INSUFFICIENT_EVIDENCE` per la v1.4; lo stress
dimensionale v2 migliora la diagnosi ma conferma il blind spot finanziario; il
dual-timescale v1 perde entrambi i mesi recessivi OOS e viene respinto senza
tuning. Il punto 7 resta un'attivita' E9 temporalmente vincolata, da eseguire
dopo il 31 luglio 2026, e non impedisce la chiusura tecnica di E10.

Checkpoint: `docs/checkpoints/0047-fase-e10-model-evidence-dual-timescale-done.md`.



### Fase E11 - Controlled Candidate Lab (COMPLETATA, 2026-07-14)

Obiettivo: usare il periodo precedente al cutoff 2026-07-31 per confrontare un
numero limitato di nuove ipotesi senza trasformare il benchmark gia' osservato
in un meccanismo di selezione post-hoc.

1. E11.1 - preregistrazione e shadow-candidate gate (COMPLETATA, 2026-07-14):
   - massimo tre famiglie e nessuno sweep non dichiarato;
   - target massimo ottenibile prima di nuovi outcome: `shadow-candidate`;
   - `operational-approved` vietato senza Evidence v2 prospettica;
   - selezione e calibrazione solo su inner rolling validation;
   - outer OOS 2008-2025 escluso dalla selezione;
   - manifest write-once con hash del gate e delle configurazioni.
2. Candidate preregistrate:
   - `baseline-v1-5-dimensional`: baseline rule-based con livello e impulso
     delle dimensioni macro-finanziarie;
   - `changepoint-duration-v1`: rilevazione causale degli shock e durata
     esplicita, senza backward smoothing;
   - `rare-event-logit-v1`: benchmark supervisionato regolarizzato, train-only,
     con trattamento preregistrato della classe rara.
3. E11.2 - implementazione delle feature temporali e della baseline v1.5
   (COMPLETATA, 2026-07-14): scenari archetipici e causalita' superati; gate
   inner-only `REJECTED_FOR_SHADOW` per Brier peggiore e mancata copertura dello
   stress protetto. Nessun parametro e' stato modificato e l'outer OOS e'
   rimasto chiuso.
4. E11.3 - implementazione dei due challenger (COMPLETATA, 2026-07-14), con
   label independence, nested validation e metriche probabilistiche condivise.
   Changepoint-duration v1 e rare-event-logit v1 sono entrambi
   `REJECTED_FOR_SHADOW`.
5. E11.4 - esecuzione consolidata del gate inner-only (COMPLETATA, 2026-07-14).
   Nessuno dei tre modelli e' eleggibile; i fallimenti sono conservati senza
   cambio di soglie e l'outer OOS resta chiuso.
6. Al primo cutoff eleggibile, la baseline v1.4 e gli eventuali shadow-candidate
   congelano previsioni parallele. Una singola osservazione non produce
   promozione operativa.

E11 non autorizza la modifica di v1.4, k-means v1, Gaussian HMM v1 o
dual-timescale v1. Ogni nuova formula o soglia richiede model id, configurazione
e manifest diversi prima dell'esecuzione.

Checkpoint E11.1:
`docs/checkpoints/0048-fase-e11-1-preregistrazione-candidate-done.md`.

Checkpoint E11.2:
`docs/checkpoints/0049-fase-e11-2-baseline-dimensionale-done.md`.

Checkpoint E11.3-E11.4:
`docs/checkpoints/0050-fase-e11-3-challenger-inner-gates-done.md`.



### Fase E12 - Event-aware task-specific candidates (COMPLETATA, 2026-07-14)

Obiettivo: provare nuovi candidati eleggibili correggendo prima il blind spot
informativo del campionamento month-end e separando i task che hanno ground
truth e costi di errore diversi.

1. E12.1 - data foundation e lifecycle (COMPLETATA, 2026-07-14):
   - aggregati point-in-time `VIX_MONTHLY_MAX`, `SOFR_EFFR_MONTHLY_MAX`,
     `SPY_MONTHLY_MAX_DRAWDOWN`, `HYG_MONTHLY_MAX_DRAWDOWN`;
   - manifest corpus v2 con coverage esplicita e nessuna imputazione della
     storia SOFR mancante;
   - contratto `e12-task-lifecycle-v1` con ruoli `recession-signal` e
     `financial-stress-signal` separati;
   - compatibilita' preservata con dataset schema v1 e baseline v1.4.
2. E12.2 - corpus reale e freeze degli input (COMPLETATA, 2026-07-14):
   - ripopolare in un nuovo layout, senza sovrascrivere il corpus v1.1;
   - costruire e validare dataset e coverage per data/fold;
   - congelare manifest e hash prima di implementare i candidate.
3. E12.3 - `event-aware-financial-stress-v1` (COMPLETATA, RESPINTA, 2026-07-14):
   - usare onset intramese, funding spread, drawdown equity/credit e HY proxy;
   - valutare inner-only contro episodi di stress protetti e falsi positivi;
   - esito massimo `ELIGIBLE_FOR_SHADOW_REVIEW`.
4. E12.4 - `sahm-yield-hazard-v1` (COMPLETATA, RESPINTA, 2026-07-14):
   - usare SAHM real-time, deterioramento INDPRO e curva dei rendimenti;
   - valutare inner-only contro NBER con metriche probabilistiche;
   - nessuna scelta basata sull'outer OOS.
5. E12.5 - decisione indipendente (COMPLETATA, 2026-07-14):
   - congelare esiti e fallimenti senza tuning post-hoc;
   - vietare la fusione se i componenti non hanno evidenza autonoma;
   - richiedere dati prospettici Evidence v2 e revisione umana per ogni stato
     oltre `shadow-candidate`.
   - esito: entrambi i componenti respinti, zero candidati shadow, fusione
     vietata e outer OOS mai aperto.

Checkpoint E12.1:
`docs/checkpoints/0051-fase-e12-1-event-aware-data-foundation-done.md`.

Checkpoint E12.2:
`docs/checkpoints/0052-fase-e12-2-corpus-coverage-freeze-done.md`.

Checkpoint E12.3:
`docs/checkpoints/0053-fase-e12-3-event-aware-financial-stress-rejected.md`.

Checkpoint E12.4:
`docs/checkpoints/0054-fase-e12-4-sahm-yield-hazard-rejected.md`.

Checkpoint E12.5:
`docs/checkpoints/0055-fase-e12-5-independent-decision-done.md`.



### Fase E13 - Constrained candidate generation (COMPLETATA, 2026-07-14)

Obiettivo: passare dalla scelta manuale di una singola formula a una famiglia
finita preregistrata, mantenendo task separati e selezione interamente inner.

1. E13.1 - grammatica e generazione (COMPLETATA, 2026-07-14):
   - congelare combinazioni ammesse, budget e vincoli prima dei punteggi;
   - generare manifest deterministico e write-once con ID content-derived;
   - vietare fusione, riuso degli ID E12 e accesso all'outer OOS;
   - esito: 16 candidati non valutati, 8 per ciascun task.
2. E13.2 - valutatore leave-one-episode-out (COMPLETATA, 2026-07-14):
   - usare esclusivamente finestre inner e lasciare fuori un episodio alla
     volta per misurare generalizzazione tra eventi;
   - selezionare le soglie soltanto nell'inner fit;
   - riportare dispersione per episodio, worst case e fallimenti di coverage.
   - esito: 8 candidati finanziari valutati su 3 episodi; 8 candidati
     recessivi non valutabili perche' nell'inner e' osservabile un solo
     episodio; outer OOS chiuso e nessuna shortlist prodotta.
3. E13.3 - shortlist Pareto (COMPLETATA, 2026-07-14):
   - penalizzare instabilita' e complessita', senza una classifica su singola
     metrica;
   - ammettere al massimo due candidati per task;
   - congelare shortlist e motivi di esclusione prima di qualunque diagnostica
     ulteriore.
   - esito: due candidati finanziari complementari congelati, uno `coverage`
     e uno `precision`; shortlist recessiva vuota per evidenza insufficiente.
4. E13.4 - gate task-specifico (COMPLETATA, RESPINTA, 2026-07-14):
   - eseguire il gate inner-only sui soli candidati congelati;
   - mantenere l'outer OOS chiuso e richiedere evidenza prospettica per ogni
     avanzamento oltre `shadow-candidate`.
   - esito: entrambi i candidati finanziari `REJECTED_FOR_SHADOW`; ramo
     recessivo non sottoposto a gate; zero candidati eleggibili.

Checkpoint E13.1:
`docs/checkpoints/0056-fase-e13-1-constrained-generator-done.md`.

Checkpoint E13.2:
`docs/checkpoints/0057-fase-e13-2-loeo-evaluation-done.md`.

Checkpoint E13.3:
`docs/checkpoints/0058-fase-e13-3-pareto-shortlist-done.md`.

Checkpoint E13.4:
`docs/checkpoints/0059-fase-e13-4-absolute-gate-rejected.md`.



### Fase E14 - Information foundation redesign (IN CORSO, 2026-07-14)

Obiettivo: correggere il problema informativo emerso in E13 prima di creare
altri candidati, separando qualita' delle feature, ontologia delle label e
copertura degli episodi.

1. E14.1 - information audit (COMPLETATA, 2026-07-14):
   - misurare separabilita' feature-per-feature e firme per episodio;
   - trattare i controlli come contrasti curati, non negativi certi;
   - mantenere outer OOS chiuso e vietare generazione/ranking;
   - esito: forte overlap broad-market, funding promettente ma fragile,
     episodi eterogenei e copertura recessiva insufficiente.
2. E14.2 - tassonomia v3 e hard-negative audit (COMPLETATA, NOT READY, 2026-07-14):
   - introdurre stati positivo, hard negative confermato e ambiguo;
   - separare broad-market, funding/liquidity, banking/credit e
     cross-border/growth;
   - versionare fonti, confini e motivazioni senza modifiche in-place.
   - esito: 6 episodi positivi, 2 ambigui e zero hard negative confermati;
     il gate informativo vieta quindi la generazione di candidati.
3. E14.3 - feasibility della nuova foundation (COMPLETATA, DOSSIER ONLY, 2026-07-14):
   - verificare estensione pre-2008, disponibilita' point-in-time e proxy
     compatibili per ottenere almeno tre episodi per detector;
   - decidere go/no-go prima di popolare un nuovo corpus.
   - esito: fonti e 5 ipotesi pre-2008 rendono plausibile la copertura positiva
     minima, ma zero hard negative bloccano la popolazione; sono autorizzati
     soltanto dossier di evidenza, non label o candidati.
4. E14.4 - contratto e dossier per meccanismo:
   - E14.4a contract audit (COMPLETATA, 2026-07-14):
     - congelare schema dei dossier e quattro detector indipendenti;
     - separare `calm`, `onset`, `active` e `recovery` con isteresi;
     - ammettere soltanto trasformazioni causali e fitting inner-only;
     - esito: `READY_FOR_DOSSIER_CURATION`, senza mutare label o corpus;
   - E14.4b1 curation positiva (COMPLETATA, REVIEWED, 2026-07-14):
     - costruiti 8 dossier hash-bound sulle 5 ipotesi positive pre-2008 e su
       ogni coppia ipotesi-meccanismo;
     - verificate fonti indipendenti, narrativa ufficiale, osservazione
       quantitativa, controevidenza e confini temporali;
     - rilevato il mismatch VIX/1987 e sostituita nel dossier la fonte con
       evidenza CFTC, senza mutare il catalogo congelato;
     - esito: 8 dossier `reviewed`, zero `accepted` e zero hard negative.
   - E14.4b2 hard-negative e review queue (COMPLETATA, 2026-07-14):
     - curati quattro hard negative affermativi, uno per meccanismo;
     - usati Brexit 2016 come contrasto broad-market, funding e cross-border
       e la crisi messicana 1994-95 come contrasto banking-credit;
     - congelati schema delle review, hash dei 12 dossier e coda write-once;
     - impedita l'auto-accettazione dell'autore dei dossier;
     - esito: copertura hard-negative completa, ma zero review indipendenti e
       stato `INDEPENDENT_REVIEW_REQUIRED`.
   - E14.4b3a handoff review (COMPLETATA, 2026-07-14):
     - generare un bundle immutabile con i 12 dossier byte-identici;
     - fornire un worksheet per dossier con evidenze, controevidenze e hash;
     - fornire template di ricevuta intenzionalmente non validi finche' il
       reviewer non completa identita', decisione e checklist;
     - esito: `AWAITING_EXTERNAL_REVIEW`, 12 worksheet e 12 template pronti.
   - E14.4b3b review indipendente e ingestione (COMPLETATA, REVISIONI RICHIESTE, 2026-07-14):
     - esaminati i 12 dossier con un agente reviewer distinto dall'autore;
     - acquisite e validate 12 ricevute hash-bound in schema v2;
     - corretta la limitazione dello schema v1 che non rappresentava una fonte
       inaccessibile come motivo valido di `needs-revision`;
     - esito: 8 `accept`, 4 `needs-revision`, 0 `reject` e stato
       `DOSSIER_REVISIONS_REQUIRED`.
   - E14.4b4 revisione mirata dossier (COMPLETATA, 2026-07-14):
     - corretti i confini di Continental Illinois e dei tre dossier Messico
       usando solo fonti istituzionali direttamente verificabili;
     - sostituito il locator FDIC problematico con il QBP FDIC 1995 Q1;
     - preservati byte-identici gli 8 dossier gia' accettati;
     - riesaminati soltanto i 4 nuovi hash: 4 `accept`, zero revisioni e zero
       rigetti;
     - esito: 12/12 dossier accettati e
       `READY_FOR_LABEL_FOUNDATION_GATE`, senza scrivere label o candidati.
   - E14.4c label-foundation gate (COMPLETATA, MERGE READY / MORE EVIDENCE REQUIRED, 2026-07-14):
     - trasformati i 12 dossier accettati in una proposta separata e
       versionata, senza mutare la ground truth v3;
     - espanse 42 label mensili per meccanismo su 24 mesi aggregati;
     - verificati zero conflitti nello stesso mese/meccanismo e zero conflitti
       con la tassonomia v3; preservati 4 mesi con stati diversi tra
       meccanismi;
     - la copertura positiva combinata supera tutte le soglie: 11 episodi
       indipendenti e rispettivamente 7/3/3/5 per broad, funding, banking e
       cross-border;
     - i quattro dossier hard-negative valgono soltanto 2 eventi indipendenti
       e 1 evento per meccanismo, sotto le soglie 6 totali e 2 per meccanismo;
     - esito: `FOUNDATION_MERGE_READY_MORE_EVIDENCE_REQUIRED`; il merge in una
       tassonomia nuova e' autorizzabile, la generazione candidati resta chiusa.
   - E14.4d taxonomy v4 (COMPLETATA, MORE HARD NEGATIVES REQUIRED, 2026-07-14):
     - materializzata una nuova tassonomia v4 dalla proposta validata, senza
       modificare in-place la v3 e mantenendo provenienza e hash dei dossier;
     - introdotto `independentEventId` per impedire che dossier dello stesso
       evento su meccanismi diversi aumentino artificialmente la copertura;
     - mantenute 12 voci monomeccanismo: 8 positive e 4 hard-negative, con
       confini temporali distinti e stati misti preservati;
     - estesa la copertura iniziale a maggio 1984 senza restringere il limite
       ereditato di dicembre 2025;
     - esito: `TAXONOMY_V4_VERSIONED_MORE_HARD_NEGATIVES_REQUIRED`, 11 eventi
       positivi e 2 hard-negative indipendenti; candidati ancora chiusi.
   - E14.4e espansione hard-negative indipendente (COMPLETATA, REVIEW REQUIRED, 2026-07-15):
     - curati quattro eventi hard-negative distinti: crash 1987 per
       banking-credit, repricing 2018Q4 per funding-liquidity, repo stress
       2019 per cross-border-growth e regional bank stress 2023 per
       broad-market-repricing;
     - preservati gli stati positivi gia' presenti sugli altri meccanismi:
       la chiave di conflitto resta `(mese, meccanismo)`, non il solo mese;
     - verificati prova affermativa di comportamento ordinato, almeno due
       provider indipendenti, controevidenza e zero conflitti;
     - preservati byte-identici i 12 manifest gia' accettati e aggiunti i 4
       nuovi hash alla review queue v6;
     - esito potenziale, non ancora accettato: 6 hard negative indipendenti e
       2 per meccanismo, con stato `INDEPENDENT_REVIEW_REQUIRED`;
     - tassonomia v4, candidati, outer OOS e promozione restano chiusi.
   - E14.4f handoff review espansione (COMPLETATA, AWAITING EXTERNAL REVIEW, 2026-07-15):
     - costruito un bundle immutabile limitato ai quattro nuovi dossier;
     - esclusi esplicitamente i 12 dossier gia' accettati, che non vengono
       riaperti;
     - generate 4 copie byte-identiche, 4 worksheet e 4 template schema v2
       intenzionalmente non ingeribili, con 12 locator complessivi;
     - impedita per contratto la review da parte del generatore e mantenuti
       chiusi coverage accettata, tassonomia, candidati e outer OOS;
     - esito: `EXPANSION_AWAITING_EXTERNAL_REVIEW`, zero ricevute.
   - E14.4g ingestione review indipendente espansione (COMPLETATA, REVISIONI RICHIESTE, 2026-07-15):
     - congelato il contratto e implementata la validazione schema v2 contro
       i quattro hash dell'handoff E14.4f;
     - preservati byte-identici i 12 accept precedenti e vietate ricevute su
       dossier estranei all'espansione;
     - un `accept` richiede fonti aperte, claim e confini confermati,
       controevidenza considerata e nessun output di modello;
     - la queue v7 viene scritta soltanto quando sono presenti esattamente
       quattro ricevute valide; un run incompleto scrive solo un audit
       retry-safe;
     - il preflight reale iniziale con 0/4 ricevute ha prodotto soltanto
       `EXPANSION_REVIEW_INCOMPLETE`, senza queue parziale;
     - un reviewer indipendente ha poi verificato tutti i 12 locator e
       prodotto quattro ricevute valide: 2 `accept`, 2 `needs-revision`, zero
       `reject`;
     - accettati 1987 banking-credit e 2018Q4 funding-liquidity;
     - da revisionare 2023 broad-market per locator IMF non direttamente
       accessibile e repo 2019 cross-border per evidenza insufficiente sul
       meccanismo di crescita reale;
     - esito: queue v7 completa e
       `EXPANSION_DOSSIER_REVISIONS_REQUIRED`; coverage, tassonomia e
       candidati restano chiusi.
   - E14.4g2 revisione mirata espansione (COMPLETATA, 2026-07-15):
     - preservati byte-identici i 14 accept complessivi e modificati soltanto
       i due manifest `needs-revision`;
     - regional-bank 2023 mantiene evento e confini, sostituendo `text.ashx`
       con il capitolo PDF IMF direttamente accessibile: rereview `accept`;
     - il dossier repo 2019 e' stato ritirato, non relabelled: gli spillover
       repo esteri non misuravano il meccanismo reale cross-border;
     - sostituito con Flash Crash 2010 cross-border, basato su CPB, WTO e
       CFTC/SEC; un primo locator PDF CPB 404 ha prodotto correttamente un
       ulteriore `needs-revision` senza aprire il gate;
     - una seconda revisione hash-scoped ha usato la pagina CPB live e il suo
       XLS ufficiale: indice world trade 154,0 ad aprile e 157,4 a maggio
       (circa +2,2%), con crescita Q2 circa +3,4%; rereview `accept`;
     - queue v11: 16/16 dossier accettati; coverage potenziale accettata per
       il prossimo gate pari a 6 eventi indipendenti e 2 per meccanismo;
     - tassonomia e candidati restano invariati: l'ingestione autorizza solo
       E14.4h, non il merge diretto.
   - E14.4h accepted hard-negative coverage gate (COMPLETATA, 2026-07-15):
     - congelati gli hash di queue v11, audit mirato v2, tassonomia v4,
       schemi e contratti di copertura/meccanismo;
     - risolti 16/16 manifest accettati contro un solo file/hash e preservati
       i 12 dossier gia' materializzati nella tassonomia v4;
     - identificati 4 nuovi hard negative accettati, quattro eventi distinti
       e un evento per ciascun meccanismo;
     - ricontata la copertura con `hypothesisId` come identita' indipendente:
       11 positivi e 6 hard negative complessivi, con 2 hard negative per
       broad-market, funding, banking e cross-border;
     - verificati zero conflitti sulla chiave `(mese, meccanismo)` e stati
       misti cross-meccanismo preservati;
     - esito `ACCEPTED_HARD_NEGATIVE_COVERAGE_READY`;
     - autorizzata soltanto una proposta di tassonomia v5; tassonomia v4,
       candidati, outer OOS e promozione restano immutati/chiusi.
   - E14.4i taxonomy v5 accepted expansion materialization (COMPLETATO):
     - creata `us-financial-stress-v5.json` come nuova versione immutabile,
       senza modificare in-place la v4;
     - incorporati quattro dossier hard-negative accettati con provenienza e
       hash congelati: 16 evidenze di fondazione complessive;
     - ricontati 11 eventi positivi e 6 hard negative indipendenti, con 2 hard
       negative per meccanismo e zero conflitti `(mese, meccanismo)`;
     - stato `TAXONOMY_V5_VERSIONED_CANDIDATE_READINESS_REQUIRED`: candidate
       generation, outer OOS e promozione restano chiusi.
   - E14.4j candidate-readiness gate (COMPLETATO):
     - verificata l'integrita' hash-bound della tassonomia v5, la copertura
       sufficiente, quattro detector indipendenti e zero conflitti;
     - rilevati quattro blocker: sei feature ancora non popolate, foundation
       point-in-time non materializzata, protocollo E13 legato alla foundation
       E12 e grammatica a due task non compatibile con quattro meccanismi;
     - esito `CANDIDATE_READINESS_BLOCKED_FOUNDATION_AND_PROTOCOL`:
       candidate generation, outer OOS e promozione restano chiusi.
   - E14.4k mechanism feature foundation (COMPLETATO):
     - congelati cinque snapshot ufficiali Cboe/FRED/FDIC e materializzate
       1.812 osservazioni in cinque serie, con sei binding sui detector;
     - TEDRATE termina a gennaio 2022 e DTWEXB a dicembre 2019 senza splicing;
       FDIC usa un lag conservativo di 60 giorni e missingness esplicita;
     - prodotto un lock immutabile con stato
       `FEATURE_FOUNDATION_MATERIALIZED_WITH_VINTAGE_LIMITATIONS`;
     - esplicitato che FRED daily e il workbook FDIC sono snapshot di storia
       corrente, non una ricostruzione vintage perfetta; candidati chiusi.
   - E14.4l taxonomy-v5 candidate protocol (COMPLETATO):
     - sostituita la grammatica E13 a due task con quattro detector autonomi e
       dieci profili, per un budget finito di 40 candidati research;
     - legato il protocollo agli hash di tassonomia v5, foundation e lock;
     - riusati i controlli causali, train-only, inner-only e missingness-explicit;
     - readiness v2 `RESEARCH_CANDIDATE_GENERATION_READY_OUTER_OOS_CLOSED`:
       autorizzata soltanto la generazione deterministica del manifest;
       fitting, evaluation, composizione, outer OOS e promozione restano chiusi.
   - definire feature relative al regime storico, onset e recovery separati;
   - definire dossier e hard negative a livello di singolo meccanismo;
   - vietare composizione finche' ogni detector non ha evidenza autonoma.
5. E14.5 - generazione condizionata (COMPLETATO):
   - generare deterministicamente i 40 candidati autorizzati, separati per
     meccanismo, senza fitting o valutazione;
   - legare ogni candidate ID al protocollo e mantenere outer OOS chiuso;
   - produrre soltanto un manifest write-once verificabile.
   - esito reale `GENERATED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED`:
     40 ID univoci e hash-bound, con conteggi 16/4/16/4; transform, fitting,
     evaluation, ranking, composizione, outer OOS e promozione restano chiusi.
6. E14.6 - preregistrazione LOEO inner per meccanismo (COMPLETATO, BLOCCO STRUTTURALE):
   - congelare fold, metriche, gestione degli episodi e regole di selezione
     delle soglie prima di eseguire qualunque fitting;
   - mantenere separati i quattro meccanismi e vietare composizione e outer OOS;
   - autorizzare fitting/evaluation inner soltanto dopo un gate dedicato.
   - esito reale: solo broad-market-repricing raggiunge la copertura minima;
     16 candidati sono strutturalmente eleggibili e 24 no;
   - fitting completo e fitting parziale restano entrambi chiusi per evitare un
     percorso broad-only non confrontabile con l'obiettivo a quattro detector.
7. E14.6a - riparazione della copertura informativa (COMPLETATO):
   - riesaminare, senza splicing opportunistico, la storia delle feature per
     banking-credit, cross-border-growth e funding-liquidity;
   - distinguere tra nuove serie point-in-time ammissibili, revisione motivata
     del requisito di 60 mesi e candidati da ritirare per evidenza insufficiente;
   - aggiornare foundation/protocollo con nuove versioni e rieseguire E14.6
     prima di qualunque fitting.
   - decisione: mantenere 60 mesi e preregistrare tre serie standalone
     FDIC failures/assistance, TWEXBMTH e Fed funds meno T-bill;
   - proiezione vincolata: 28 candidati eleggibili (16 broad esistenti e 12
     nuovi), da verificare sui dati materializzati; generazione e fitting chiusi.
8. E14.6b - materializzazione feature foundation v2 (COMPLETATO):
   - scaricare e congelare tramite hash le tre fonti ufficiali preregistrate;
   - materializzare le serie senza mutare foundation v1 e verificare copertura,
     missingness, zeri osservati e confini metodologici;
   - eseguire diagnostiche di revisione e di cambio fonte/metodologia;
   - produrre foundation v2 e lock v2, mantenendo candidate generation chiusa.
   - esito reale: 3.437 osservazioni, 69 missing FDIC espliciti e copertura
     positiva/hard-negative 3/2 banking, 6/2 broad, 5/2 cross e 3/2 funding;
   - la copertura strutturale e' riparata, ma `strictVintageReady` resta falso
     per assenza di snapshot point-in-time confrontabili; fitting e generation
     restano chiusi.
9. E14.6c - structural readiness gate v2 (COMPLETATO):
   - vincolare il gate agli hash di foundation v2, lock v2 e audit v2;
   - rieseguire l'eleggibilita' sui dati reali includendo missingness interna e
     disponibilita' mensile, senza riusare gli ID ritirati;
   - congelare la sensitivity policy sul confine `TB3SMFFM` 2019 e mantenere
     esplicito il rischio di revisione current-history;
   - autorizzare al massimo la stesura del protocollo/manifest v2, non fitting,
     evaluation o outer OOS.
   - esito reale: 28/28 ingressi eleggibili, con 16 ID broad preservati, 24 ID
     v1 ritirati e 12 nuovi ID v2 pianificati ma non generati;
   - policy funding 2019 congelata come sensitivity inner obbligatoria e non
     come gate alternativo; protocol design aperto, manifest generation chiusa.
10. E14.6d - protocollo di candidate generation v2 (COMPLETATO):
   - congelare grammatica, profili, persistenza e soglie sui 28 ID del roster;
   - preservare esattamente i 16 oggetti broad compatibili e usare i 12 ID v2
     senza ricalcolarli o riusare i 24 ID ritirati;
   - incorporare missingness, lag di disponibilita', sensitivity funding 2019
     e rischio revisioni current-history nel protocollo;
   - autorizzare al massimo la successiva materializzazione del manifest v2,
     mantenendo fitting, evaluation, ranking e outer OOS chiusi.
   - esito reale: protocollo congelato su 28 ID nello stesso ordine del roster,
     7 profili e quattro combinazioni di persistenza per profilo;
   - aperta soltanto la materializzazione write-once del manifest v2.
11. E14.6e - materializzazione candidate manifest v2 (COMPLETATO):
   - copiare verbatim i 28 ingressi del roster nel manifest, cambiando soltanto
     il lifecycle in `research-generated-not-fit`;
   - verificare identita', ordine, profili, binding, eligibility e persistenza
     contro protocollo v2 e roster, senza ricalcolo degli ID;
   - produrre manifest e generation audit write-once hash-bound;
   - mantenere trasformazione, fitting, evaluation, ranking, composizione e
     outer OOS chiusi.
   - esito reale: manifest write-once materializzato con 28 candidati
     (4 banking, 16 broad, 4 cross-border, 4 funding) nello stesso ordine di
     roster e protocollo;
   - tutti i campi sono copiati verbatim; la sola transizione e'
     `readiness-planned-not-generated-not-fit` -> `research-generated-not-fit`;
   - generation audit positivo, zero feature trasformate, zero righe outer e
     fitting/evaluation/ranking ancora chiusi.
12. E14.6f - preregistrazione fitting e LOEO v2 (COMPLETATO):
   - congelare dataset, fold leave-one-episode-out, trasformazioni train-only,
     gate assoluti per meccanismo e sensitivity funding 2019;
   - autorizzare il fitting inner-only soltanto dopo verifica hash-bound di
     manifest, protocollo e foundation v2;
   - mantenere outer OOS, composizione e promozione chiusi.
   - esito reale: 28/28 candidati eleggibili e 140 assegnazioni LOEO congelate
     (12 banking, 96 broad, 20 cross-border, 12 funding);
   - gate assoluti, soglie q80/q90/q95 train-only, diagnostica funding 2019 e
     controllo snapshot drift sono congelati prima del fitting;
   - autorizzati per il solo passo successivo trasformazioni causali, fitting e
     evaluation inner-only; nessuna di queste operazioni e' stata ancora
     eseguita e ranking, outer OOS, composizione e promozione restano chiusi.
13. E14.6g - esecuzione fitting e LOEO v2 (COMPLETATO, NO-GO):
   - calcolare trasformazioni causali sui soli training row di ciascun fold;
   - selezionare soglie e fittare i 28 candidati separatamente per meccanismo;
   - valutare i 140 fold preregistrati, produrre metriche assolute e sensitivity
     funding 2019 senza ranking o accesso all'outer OOS.
   - esito reale: 28/28 candidati valutati sui 140 fold congelati, con
     trasformazioni percentile causali midrank, missingness esplicita e soglie
     q80/q90/q95 selezionate solo sui training score;
   - zero candidati supera tutti i gate assoluti in ciascuno dei quattro
     meccanismi; il migliore banking raggiunge hit rate 0,667 e mean recall
     0,50 ma worst recall 0, mentre broad, cross-border e funding restano
     rispettivamente a hit rate massimo 0,167, 0,40 e 0;
   - sensitivity funding completa su 12 fold-candidato, inclusi confronti
     q80/q90/q95 full/pre-2019 e metriche episodio pre/post;
   - ranking, shortlist, composizione, outer OOS e promozione restano chiusi.
14. E14.6h - consolidamento no-go e nuova ipotesi informativa (COMPLETATO):
   - decomporre i fallimenti per episodio, profilo e componente informativa;
   - distinguere assenza di segnale, direzione/trasformazione inadeguata e
     label eterogenee senza ritoccare post-hoc soglie o gate;
   - decidere se chiudere E14 con no-go oppure preregistrare una nuova
     foundation/candidate grammar prima di qualsiasi nuova valutazione.
   - esito: zero fallimenti del gate hard-negative e zero fallimenti di
     threshold range; il limite dominante e' esclusivamente la generalizzazione
     positiva cross-episode, con worst recall zero per tutti i 28 candidati;
   - banking manca interamente euro-sovereign 2011, broad manca 5 episodi su 6,
     cross-border 3 su 5 e funding tutti e 3;
   - chiusa con no-go l'intera famiglia v2 esistente; autorizzato soltanto il
     design preregistrato di una nuova ipotesi informativa, senza materializzare
     dati, generare o rivalutare candidati.
15. E14.7 - preregistrazione nuova ipotesi informativa (COMPLETATO):
   - definire famiglie feature complementari per meccanismo con firme attese
     episodio per episodio e fonti verificabili;
   - separare onset, intensita' e recovery e congelare direzione, trasformazione
     e ablation prima di popolare nuovi dati;
   - mantenere taxonomy v5, gate, fitting, ranking, composizione e outer OOS
     immutati/chiusi fino a un nuovo readiness audit.
   - esito: congelate 8 famiglie informative, due per meccanismo, basate su 10
     fonti verificabili e accompagnate da 17 firme onset/intensita'/recovery,
     una per ogni episodio positivo usato nel LOEO v2;
   - banking aggiunge deterioramento patrimoniale e flussi di bilancio;
     broad aggiunge drawdown azionario e dispersione creditizia; cross-border
     aggiunge dollar shock BIS e contrazione dei flussi bancari internazionali;
     funding aggiunge tiering commercial paper e dislocazione repo SOFR-era;
   - preregistrate falsification condition, regimi metodologici, missingness e
     ablation prima della popolazione. Nessuna fonte e' stata scaricata e
     taxonomy, foundation, generation, fitting, evaluation e outer restano
     chiusi.
16. E14.7a - source and vintage feasibility audit (COMPLETATO, BLOCCATO):
   - verificare accessibilita', licenza, copertura episodio per episodio,
     release/vintage semantics e correzioni delle 10 fonti preregistrate;
   - classificare ogni famiglia `ready`, `conditional` o `blocked` senza
     sostituzioni fallback suggerite dai risultati;
   - autorizzare l'acquisizione soltanto con un successivo contratto separato;
     E14.7a resta read-only rispetto ai dati di ricerca.
   - esito fonti: 1 `ready`, 5 `conditional`, 4 `blocked`; esito famiglie:
     0 `ready`, 3 `conditional`, 5 `blocked`;
   - i tre blocchi strutturali di storia causale sono FDIC aggregate per
     Continental Illinois (4/60 mesi), commercial paper per Russia/LTCM
     (19/60) e SOFR repo per settembre 2019 (17/36); si aggiungono i blocchi
     licenza Nasdaq/Moody's e la copertura storica incompleta del volume CP;
   - restano condizionali H.8, BIS effective exchange rates e BIS locational
     banking statistics per vintage/release semantics non ancora provati;
   - nessuna acquisizione autorizzata. Le cinque famiglie bloccate sono
     ritirate senza fallback e le tre condizionali restano congelate.
17. E14.7b - feasibility remediation preregistration (COMPLETATO):
   - conservare immutate le tre famiglie condizionali e definire i soli task
     documentali necessari per vintage, release archive e methodology manifest;
   - ritirare formalmente le cinque famiglie bloccate e preregistrare eventuali
     sostituzioni motivate indipendentemente, senza riutilizzare i dati o gli
     esiti LOEO per scegliere ex post la fonte;
   - mantenere download, foundation, candidati, fitting, evaluation e outer OOS
     chiusi fino a un nuovo gate di fattibilita' completo.
   - esito: preservate esattamente le 3 famiglie condizionali con task
     documentali espliciti e ritirate senza fallback le 5 famiglie bloccate;
   - preregistrate 5 sostituzioni indipendenti basate su 7 fonti ufficiali:
     statistiche storiche annuali FDIC, Z.1 Fed, DGS2/DGS10, DCD90/DTB3 e
     statistiche primary dealer della New York Fed;
   - tutte le sostituzioni rispettano nominalmente la storia causale minima
     congelata, ma la copertura nominale non costituisce readiness: licenza,
     vintage, release semantics e metodologia devono essere riesaminati;
   - nessuna osservazione scaricata, nessun dato di valutazione/outer usato e
     nessuna modifica a taxonomy, soglie o gate.
18. E14.7c - replacement and conditional source feasibility re-audit
    (COMPLETATO, BLOCCATO):
   - raccogliere e congelare prove provider-primary per le 3 famiglie
     condizionali e le 7 fonti delle 5 sostituzioni;
   - verificare licenza, copertura componente, data di pubblicazione, vintage,
     revisioni e regimi metodologici senza scaricare osservazioni di ricerca;
   - autorizzare una successiva acquisizione solo se ogni famiglia risulta
     `ready`; in caso contrario chiudere il ramo o preregistrare un'ulteriore
     remediation senza fallback post-hoc.
   - esito fonti: 1 `ready` (`fred-dtb3`) e 9 `blocked`; esito famiglie:
     0 `ready` e 8 `blocked`;
   - H.8 non prova release pre-1984; gli archivi online Z.1 iniziano nel 1996
     e ALFRED documenta DGS2/DGS10/DTB3 soltanto dal 2005; BIS EER/LBS non
     offre vintages provider-primary completi per tutti gli episodi;
   - FDIC annual historical e primary dealer NY Fed hanno copertura nominale,
     ma non chiudono insieme componenti, termini di snapshot, revisioni e
     release storiche immutabili;
   - nessuna acquisizione autorizzata: la copertura osservazionale lunga non
     sostituisce la disponibilita' event-time verificabile.
19. E14.7d - vintage-policy decision preregistration (COMPLETATO):
   - scegliere prima di qualsiasi dato fra chiusura E14, ricostruzione
     archivistica finanziata mantenendo lo standard corrente, oppure uno scope
     di ricerca post-2005 separatamente versionato;
   - quantificare perdita di episodi e identificabilita' per ogni opzione,
     senza usare osservazioni, LOEO o outer OOS per scegliere la policy;
   - vietare qualsiasi rilassamento implicito della causalita' o sostituzione
     della publication availability con la sola observation date.
   - esito: selezionato condizionalmente uno scope di ricerca separato con
     cutoff immutabile `2006-01-01`; il ramo E14 storico resta chiuso;
   - scartata la chiusura immediata perche' esiste ancora un esperimento
     identificabile; ricostruzione archivistica rinviata a backlog finanziato
     perche' incompatibile con la finestra fino al 31 luglio;
   - preservati 6 eventi positivi unici e 10 assegnazioni meccanismo-evento,
     con almeno 2 positivi per ciascun meccanismo;
   - hard negative post-cutoff: banking 0, broad 2, cross-border 2, funding 2;
     lo scope non e' attivo e servono 2 nuovi controlli banking indipendenti;
   - taxonomy v5, fonti, dataset, fitting, evaluation e outer OOS restano
     immutati/chiusi.
20. E14.7e - post-2005 scope and banking hard-negative feasibility
    (COMPLETATO):
   - preregistrare criteri e candidati documentali per almeno 2 hard negative
     banking-credit post-2005, indipendenti dai positivi e dagli esiti modello;
   - riesaminare la disponibilita' source/vintage nel nuovo scope senza
     acquisire osservazioni e senza ereditare automaticamente le famiglie
     bloccate E14.7c;
   - autorizzare una proposta di taxonomy separata soltanto se positivi,
     controlli e fonti raggiungono la fattibilita' minima congelata.
   - esito controlli: `london-whale-contained-2012` e
     `archegos-contained-2021` sono due candidati documentali indipendenti,
     post-cutoff e senza sovrapposizione con finestre positive;
   - entrambi hanno evidenza evento provider-primary ed evidenza separata di
     contenimento sistemico; non sono ancora label accettate in taxonomy;
   - conteggi dopo i candidati: positivi 2/4/2/2 e hard negative 2/2/2/2 per
     banking, broad, cross-border e funding;
   - pronte esattamente 4 famiglie di fattibilita', una per meccanismo: H.8/QBP
     archiviati, DGS2-DGS10 con vintages ALFRED post-2005, H.10 release archive
     e DCPF3M-DTB3 con regimi CP espliciti;
   - lo scope non e' attivo: e' autorizzata soltanto la preregistrazione di una
     proposta taxonomy separata e della relativa review indipendente.
21. E14.7f - post-2005 taxonomy proposal and independent-review queue
    (COMPLETATO):
    - materializzare una proposta con identificatori nuovi senza mutare
      `us-financial-stress-v5.json`;
    - creare dossier hash-bound per i due controlli banking e una queue
      write-once per revisori indipendenti;
    - mantenere acquisizione osservazioni, foundation, candidati, evaluation e
      outer OOS chiusi fino all'accettazione esplicita della proposta.
    - esito: proposta `us-financial-stress-post2005-v1` inattiva con 6 positivi
      referenziati, 6 hard negative legacy e 2 nuovi controlli banking;
    - queue con 2 dossier, 0 receipt e self-acceptance vietata;
    - taxonomy v5 byte-identica e tutti gli output hash-bound/write-once.
22. E14.7g - independent-review handoff and receipt ingestion
    (IN CORSO - HANDOFF COMPLETATO, RECEIPT ESTERNE PENDENTI):
    - consegnare queue, proposta e dossier byte-identici a un reviewer
      indipendente dal curatore;
    - accettare soltanto receipt conformi allo schema v2 e con SHA-256 dossier
      esatto, senza auto-accettazione o sostituzione degli artefatti;
    - lasciare lo scope inattivo in caso di reject, needs-revision, receipt
      mancante o hash mismatch; nessuna acquisizione dati e' autorizzata.
    - E14.7g1 completato: bundle con proposta e queue byte-identiche, 2 dossier,
      2 worksheet e 2 template schema v2 intenzionalmente non ingeribili;
    - audit handoff SHA-256
      `0bf1cbcc51ca8cbf9c7eee7e3bae228a1b0cf1dfad0464b8c6aebf856beb8243`;
    - readiness ingestion con 0 receipt: stato fail-closed
      `POST_2005_INDEPENDENT_REVIEW_INCOMPLETE`, scope inattivo;
    - prossimo passo esterno: un reviewer realmente indipendente deve aprire
      tutti i locator e restituire le 2 receipt v2 fuori dal bundle immutabile.

Analisi E14:
`docs/e14-riesame-problema-informativo.md`.

Checkpoint E14.1:
`docs/checkpoints/0060-fase-e14-1-information-audit-done.md`.

Checkpoint E14.2:
`docs/checkpoints/0061-fase-e14-2-tristate-label-audit-done.md`.

Checkpoint E14.3:
`docs/checkpoints/0062-fase-e14-3-historical-feasibility-done.md`.

Checkpoint E14.4a:
`docs/checkpoints/0063-fase-e14-4a-mechanism-contract-done.md`.

Checkpoint E14.4b1:
`docs/checkpoints/0064-fase-e14-4b1-positive-dossiers-reviewed.md`.

Checkpoint E14.4b2:
`docs/checkpoints/0065-fase-e14-4b2-hard-negatives-review-queue.md`.

Checkpoint E14.4b3a:
`docs/checkpoints/0066-fase-e14-4b3a-external-review-handoff.md`.

Checkpoint E14.4b3b:
`docs/checkpoints/0067-fase-e14-4b3b-independent-review-ingested.md`.

Checkpoint E14.4b4:
`docs/checkpoints/0068-fase-e14-4b4-targeted-revision-accepted.md`.

Checkpoint E14.4c:
`docs/checkpoints/0069-fase-e14-4c-label-foundation-gate.md`.

Checkpoint E14.4d:
`docs/checkpoints/0070-fase-e14-4d-taxonomy-v4-versioned.md`.

Checkpoint E14.4e:
`docs/checkpoints/0071-fase-e14-4e-hard-negative-expansion-curated.md`.

Checkpoint E14.4f:
`docs/checkpoints/0072-fase-e14-4f-expansion-review-handoff.md`.

Checkpoint E14.4g:
`docs/checkpoints/0073-fase-e14-4g-expansion-review-ingestion-ready.md`.

Checkpoint review E14.4g:
`docs/checkpoints/0074-fase-e14-4g-expansion-review-ingested.md`.

Checkpoint E14.4g2:
`docs/checkpoints/0075-fase-e14-4g2-targeted-expansion-accepted.md`.

Checkpoint E14.4h:
`docs/checkpoints/0076-fase-e14-4h-accepted-coverage-gate.md`.

Checkpoint E14.4i:
`docs/checkpoints/0077-fase-e14-4i-taxonomy-v5-versioned.md`.

Checkpoint E14.4j:
`docs/checkpoints/0078-fase-e14-4j-candidate-readiness-blocked.md`.

Checkpoint E14.4k:
`docs/checkpoints/0079-fase-e14-4k-feature-foundation-materialized.md`.

Checkpoint E14.4l:
`docs/checkpoints/0080-fase-e14-4l-four-detector-protocol-ready.md`.

Checkpoint E14.5:
`docs/checkpoints/0081-fase-e14-5-candidate-manifest-generated.md`.

Checkpoint E14.6:
`docs/checkpoints/0082-fase-e14-6-loeo-preregistered-coverage-blocked.md`.

Checkpoint E14.6a:
`docs/checkpoints/0083-fase-e14-6a-coverage-repair-preregistered.md`.

Checkpoint E14.6b:
`docs/checkpoints/0084-fase-e14-6b-feature-foundation-v2-materialized.md`.

Checkpoint E14.6c:
`docs/checkpoints/0085-fase-e14-6c-readiness-v2-passed.md`.

Checkpoint E14.6d:
`docs/checkpoints/0086-fase-e14-6d-protocol-v2-ready.md`.

Checkpoint E14.6e:
`docs/checkpoints/0087-fase-e14-6e-candidate-manifest-v2-generated.md`.

Checkpoint E14.6f:
`docs/checkpoints/0088-fase-e14-6f-loeo-v2-preregistered.md`.

Checkpoint E14.6g:
`docs/checkpoints/0089-fase-e14-6g-loeo-v2-no-go.md`.

Checkpoint E14.6h:
`docs/checkpoints/0090-fase-e14-6h-no-go-diagnostic.md`.

Checkpoint E14.7:
`docs/checkpoints/0091-fase-e14-7-new-information-preregistered.md`.

Checkpoint E14.7a:
`docs/checkpoints/0092-fase-e14-7a-source-vintage-feasibility-blocked.md`.

Checkpoint E14.7b:
`docs/checkpoints/0093-fase-e14-7b-feasibility-remediation-preregistered.md`.

Checkpoint E14.7c:
`docs/checkpoints/0094-fase-e14-7c-replacement-source-feasibility-blocked.md`.

Checkpoint E14.7d:
`docs/checkpoints/0095-fase-e14-7d-vintage-policy-post-2005-selected.md`.

Checkpoint E14.7e:
`docs/checkpoints/0096-fase-e14-7e-post2005-scope-feasible.md`.

Checkpoint E14.7f:
`docs/checkpoints/0097-fase-e14-7f-post2005-taxonomy-proposal-ready.md`.

Checkpoint E14.7g1:
`docs/checkpoints/0098-fase-e14-7g1-review-handoff-ready.md`.

Checkpoint E14.7g-E14.7h:
`docs/checkpoints/0099-fase-e14-7g-review-revision-and-scope-activation.md`.

Checkpoint E14.7i:
`docs/checkpoints/0100-fase-e14-7i-source-acquisition-manifest-frozen.md`.

Checkpoint E14.7j:
`docs/checkpoints/0101-fase-e14-7j-source-execution-gate-authorized.md`.

Checkpoint E14.7k:
`docs/checkpoints/0102-fase-e14-7k-atomic-source-snapshot-acquired.md`.

Checkpoint E14.7l:
`docs/checkpoints/0103-fase-e14-7l-vintage-fitness-partial.md`.

Checkpoint E14.7m:
`docs/checkpoints/0104-fase-e14-7m-vintage-remediation-blocked.md`.

Checkpoint E14.7n:
`docs/checkpoints/0105-fase-e14-7n-policy-redesign-awaiting-review.md`.

Checkpoint E14.7o:
`docs/checkpoints/0106-fase-e14-7o-policy-redesign-handoff-blocked.md`.

Checkpoint E14.7p:
`docs/checkpoints/0107-fase-e14-7p-policy-redesign-review-remediated.md`.

Checkpoint E14.7q:
`docs/checkpoints/0108-fase-e14-7q-policy-redesign-review-handoff-ready.md`.

Checkpoint E14.7r:
`docs/checkpoints/0109-fase-e14-7r-policy-redesign-review-ingested.md`.

Checkpoint E14.7s:
`docs/checkpoints/0110-fase-e14-7s-policy-redesign-activated.md`.

Checkpoint E14.7t:
`docs/checkpoints/0111-fase-e14-7t-source-manifest-request-catalog-v2.md`.

Checkpoint E14.7u:
`docs/checkpoints/0112-fase-e14-7u-metadata-execution-gate-v2.md`.

Checkpoint E14.7v:
`docs/checkpoints/0113-fase-e14-7v-acquisition-discovery-preflight.md`.

Checkpoint E14.7w:
`docs/checkpoints/0114-fase-e14-7w-acquisition-remediation-docket.md`.

Checkpoint E14.7x:
`docs/checkpoints/0115-fase-e14-7x-acquisition-remediation-reviewed.md`.

Checkpoint E14.7y:
`docs/checkpoints/0116-fase-e14-7y-fdic-metadata-collection-preregistered.md`.

Checkpoint E14.7z:
`docs/checkpoints/0117-fase-e14-7z-fdic-metadata-design-reviewed.md`.

Checkpoint E14.7aa:
`docs/checkpoints/0118-fase-e14-7aa-fdic-metadata-execution-gate.md`.

Checkpoint E14.7ab:
`docs/checkpoints/0119-fase-e14-7ab-fdic-metadata-collection-preflight-blocked.md`.

Checkpoint E14.7ac:
`docs/checkpoints/0120-fase-e14-7ac-fdic-metadata-request-catalog-preregistered.md`.

Checkpoint E14.7ad:
`docs/checkpoints/0121-fase-e14-7ad-fdic-metadata-request-catalog-review-blocked.md`.



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
