# Macro Regime - Fase A: Consolidamento storico e confronto run - Done

Data: 2026-07-09

## Scopo della fase

La Fase A del piano operativo (`docs/0001-piano-operativo.md`) chiude i tre limiti principali rimasti aperti dalla prima release informativa:

1. il dettaglio di una run storica veniva ottenuto rieseguendo la pipeline invece di leggere il record salvato;
2. non esisteva un confronto tra due run;
3. la Web UI non aveva un progetto di test dedicato.

La fase resta coerente con le decisioni precedenti: nessun database, nessuna rete runtime, persistenza file-based, Domain invariato, Application estesa solo tramite porte, Web read-only.

## Cosa e' stato realizzato

### Schema run JSON v2

Il file `regime-run-{data}.json` ora persiste la run completa:

- snapshot regime (come in v1);
- `dataSource` (kind, description, reference);
- `allocation` (suggestion, turnover, estimated cost, righe per asset class, rationale, constraint).

Governance dello schema:

- `schemaVersion` portata a 2;
- lettura retrocompatibile dei file v1 (allocation e data source risultano assenti e la UI lo dichiara);
- schema version non supportata rifiutata con errore esplicito.

### Porta e read model applicativi

- `IRegimeRunStore` ora espone `SaveAsync(RegimeRunDocument)` e `LoadAsync(asOfDate)`.
- Nuovo read model `RegimeRunDocument` in Application: rappresenta la run persistita cosi' com'e', senza ricostruire aggregati di dominio da dati parziali.
- Il salvataggio della run e' stato spostato da `CalculateRegimeUseCase` a `RunRegimeAnalysisUseCase`, che salva il documento completo dopo la proposta allocativa. `CalculateRegimeUseCase` torna a essere puro calcolo.

### Nuovi use case

- `LoadRegimeRunUseCase`: apre una run storica dal JSON salvato, senza rieseguire la pipeline.
- `CompareRegimeRunsUseCase`: confronta due run salvate e produce delta su regime primario/operativo, confidence, composite score, probabilita' per regime, feature score normalizzati e proposta allocativa (suggestion, turnover, costo, target per asset class). Gestisce il caso di run v1 senza allocation.

### Web UI

- La colonna `Open` della Run History apre ora `/RunDetail?asOfDate=...`, che legge il JSON salvato: la pagina dichiara esplicitamente "Loaded from saved run JSON without re-executing the pipeline" e mostra regime, probabilita', feature, explanation, allocation, warning, artifact e report markdown salvato.
- Nuova pagina `/CompareRuns`: selezione di due date, riepilogo variazioni regime/confidence/composite, tabelle delta probabilita', delta feature e confronto allocation, con link ai dettagli delle due run.
- Link `Compare runs` nella barra di navigazione e nella Run History.
- La dashboard `/` resta il punto in cui una run viene eseguita/rieseguita.

### Test Web dedicati

Nuovo progetto `tests/MacroRegime.Web.Tests` con `WebApplicationFactory`:

- dashboard esegue la pipeline e rende il regime;
- run detail carica la run salvata dal JSON;
- run detail segnala run mancante;
- compare confronta due run salvate;
- compare segnala baseline mancante.

Il progetto usa un output directory temporanea e fallback demo per le date senza dati importati.

## Verifiche eseguite

Build:

```text
dotnet build MacroRegime.slnx --no-restore
```

Esito: build superata, 0 warning, 0 errori.

Test:

```text
dotnet test MacroRegime.slnx --no-restore
```

Esito:

- `MacroRegime.Domain.Tests`: 79 test superati;
- `MacroRegime.Application.Tests`: 24 test superati;
- `MacroRegime.Infrastructure.Tests`: 27 test superati;
- `MacroRegime.Reporting.Tests`: 2 test superati;
- `MacroRegime.Cli.Tests`: 4 test superati;
- `MacroRegime.Web.Tests`: 5 test superati;
- totale: 141 test superati, 0 falliti.

Smoke CLI:

- run completata su dati sample con `--strict-data --strict-config`;
- run JSON generato con `schemaVersion: 2`, sezioni `dataSource` e `allocation` presenti.

Smoke Web:

- `/` risponde 200;
- `/RunDetail?asOfDate=2026-07-01` risponde 200, contiene `Stored Run Detail`, `Loaded from saved run JSON`, `Goldilocks`, `Allocation Proposal`, `PartialRebalance`;
- `/CompareRuns` risponde 200 con elenco run indicizzate;
- `/CompareRuns` con baseline inesistente segnala `No stored run found`.

Gate architetturali:

- Domain invariato;
- Application senza dipendenze da Infrastructure/Web/filesystem concreto (il read model e le porte restano astrazioni);
- nessun database, nessuna rete runtime;
- nessun project reference vietato nei layer core.

## Cosa resta fuori

- Report di validazione import/config separato (Fase B);
- dataset macro storici reali e import multi-data (Fase B);
- decisione database locale (Fase C);
- provider esterni, research lab, backtesting, stress test (Fasi D-F).

## Valutazione

Fase A completata. La dashboard non e' piu' l'unico punto di consultazione: lo storico e' consultabile e confrontabile direttamente dai record salvati, e la Web UI e' coperta da test automatici. La prossima fase consigliata e' la Fase B (import dati e diagnostica).
