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

Il dettaglio per ogni step e' in `docs/checkpoints/` (progressivi 0001-0031).

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
4. Metriche composite: regime accuracy vs NBER, asset alignment 4-13 settimane, tilt simulation, penalita' asimmetrica sui falsi negativi in Stagflazione e Deflation/Bust.
5. Promozione di un challenger solo tramite Model Gate con model card.

Gate dati introdotto nella Slice 1:

- validazione schema e coerenza dei forward returns;
- controlli point-in-time su observation/publication/availability date;
- manifest con hash, dimensione, copertura, simboli e orizzonti;
- nessun fold completo se il dataset copre meno di 12 anni;
- sample demo esclusi da qualunque Model Gate.

La Slice 2 ha popolato e manifestato il dataset reale pluriennale: 213 snapshot macro mensili, 4.536 snapshot market giornalieri, 3.834 forward return e 6 fold rolling. Il corpus locale e' sotto `data/historical-real-2008-2025/` ed e' escluso da Git; gli artefatti sono identificati da SHA-256.

Restano prioritari per le prossime slice: ground truth NBER/cronologia crisi versionata, primo challenger con model card e confronto con la baseline, indice operativo incrementale per corpus grandi, integrazione persistita del calendario release e stress test successivi.

Checkpoint Slice 1: `docs/checkpoints/0029-fase-e-slice1-research-data-gate-done.md`.

Checkpoint Slice 2: `docs/checkpoints/0030-fase-e-slice2-dataset-reale-pluriennale-done.md`.

Checkpoint Slice 3: `docs/checkpoints/0031-fase-e-slice3-baseline-walk-forward-done.md`.



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
