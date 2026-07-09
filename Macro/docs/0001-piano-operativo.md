# Macro-Regime Engine - Piano operativo completo

Data: 2026-07-09

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
research/regime-eval/          (futuro) research lab Python
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

Il dettaglio per ogni step e' in `docs/checkpoints/` (progressivi 0001-0022).

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



### Fase C - Decisione persistenza

1. Valutare se e quando introdurre un database locale (ADR dedicata).
2. In caso positivo, introdurre la persistenza solo come adapter in Infrastructure, senza toccare Domain e Application.
3. In caso negativo, formalizzare il file-based come scelta di lungo periodo.



### Fase D - Provider dati esterni

1. Adapter FRED/ALFRED dietro le porte applicative esistenti.
2. Gestione vintage reale e calendario rilasci.
3. Nessuna rete nel runtime core: il download resta un adapter isolato.



### Fase E - Research lab e modelli challenger

1. Creare `research/regime-eval/` con protocollo di valutazione (Python; il runtime resta C#).
2. Walk-forward obbligatorio: train 10 anni, test 2 anni, avanzamento 1 anno; nessuna selezione iperparametri sul test.
3. Challenger: HMM, Markov switching, clustering, jump model; sempre confrontati con la baseline rule-based.
4. Metriche composite: regime accuracy vs NBER, asset alignment 4-13 settimane, tilt simulation, penalita' asimmetrica sui falsi negativi in Stagflazione e Deflation/Bust.
5. Promozione di un challenger solo tramite Model Gate con model card.



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

