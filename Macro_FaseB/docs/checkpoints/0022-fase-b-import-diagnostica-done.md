# Macro Regime - Fase B: Import dati e diagnostica - Done

Data: 2026-07-09

## Scopo della fase

La Fase B del piano operativo (`docs/0001-piano-operativo.md`) consolida import dati e diagnostica dopo la chiusura della Fase A. Gli obiettivi erano:

1. generare un report di validazione import/config separato e leggibile;
2. estendere i dataset locali oltre il singolo sample demo, abilitando un percorso verso serie storiche locali;
3. introdurre un import storico multi-data per popolare il manifest con piu' as-of date.

La fase resta file-based, senza database e senza rete runtime. Il Domain non e' stato modificato.

## Cosa e' stato realizzato

### Report diagnostico import/config

Sono stati introdotti:

- `ValidateImportCommand`;
- `ImportValidationReport`;
- `ImportValidationItem`;
- `ImportValidationSeverity`;
- porta `IImportValidationService`;
- adapter `JsonImportValidationService`;
- renderer `ImportValidationMarkdownRenderer`.

La diagnostica valida i sei input locali:

- macro data;
- model version;
- feature set;
- allocation policy;
- current portfolio;
- tilt rules.

Per ogni input il report indica severity `Ok`, `Warning` o `Error`, path e messaggio leggibile. I warning coprono fallback non bloccanti; gli errori coprono file mancanti in strict mode, JSON non valido, schema non supportato e mismatch as-of dove applicabile.

### CLI validate-only

La CLI supporta ora:

- `--validate-only`;
- `--validate-report <path>`.

Il comando produce un report markdown senza eseguire la pipeline e senza scrivere run/report di analisi. Exit code:

- `0` se non ci sono errori diagnostici;
- `2` se la validazione rileva errori.

### CLI batch multi-data

La CLI supporta ora:

- `--batch-from yyyy-MM-dd`;
- `--batch-to yyyy-MM-dd`;
- `--data-dir <path>`;
- `--portfolio-dir <path>`.

Il batch usa la convenzione:

- `macro-data-yyyy-MM-dd.json`;
- `current-portfolio-yyyy-MM-dd.json`.

Per ogni data esegue la pipeline esistente, salva run JSON/report markdown e aggiorna il manifest. Il batch continua sulle date successive in caso di errore su una data e chiude con riepilogo successi/fallimenti.

### Web UI diagnostica

E' stata aggiunta la pagina read-only:

- `/ImportDiagnostics`

La pagina mostra:

- form as-of;
- stato complessivo della validazione;
- contatori OK/warning/error;
- tabella input/severity/messaggio/path;
- report markdown completo.

La barra di navigazione include il link `Import diagnostics`.

## Verifiche eseguite

Build:

```text
dotnet build MacroRegime.slnx --no-restore
```

Esito:

- build superata;
- 0 warning;
- 0 errori.

Test:

```text
dotnet test MacroRegime.slnx --no-restore
```

Esito:

- `MacroRegime.Domain.Tests`: 79 test superati;
- `MacroRegime.Application.Tests`: 24 test superati;
- `MacroRegime.Infrastructure.Tests`: 32 test superati;
- `MacroRegime.Reporting.Tests`: 2 test superati;
- `MacroRegime.Cli.Tests`: 7 test superati;
- `MacroRegime.Web.Tests`: 6 test superati;
- totale: 150 test superati, 0 falliti.

Smoke CLI validate-only:

- comando con dati sample e `--strict-data --strict-config`;
- report markdown generato;
- report contiene `# Import Validation Report`;
- `OK: 6`;
- `Errors: 0`.

Smoke CLI batch:

- batch `2026-07-01` - `2026-07-02`;
- due run completate con `Goldilocks` e `PartialRebalance`;
- `regime-run-2026-07-01.json` generato;
- `regime-run-2026-07-02.json` generato;
- `manifest.json` generato.

Smoke Web:

- `/ImportDiagnostics?asOfDate=2026-07-01` risponde `200`;
- pagina contiene `Import Diagnostics`;
- pagina contiene `Import Validation Report`;
- pagina contiene `Macro data`;
- pagina contiene `Current portfolio`;
- pagina contiene `OK:`.

Gate architetturali:

- Domain invariato;
- nessun database introdotto;
- nessuna rete runtime introdotta;
- diagnostica esposta tramite porta applicativa;
- Infrastructure resta responsabile di JSON/filesystem;
- Web resta read-only.

## Cosa resta fuori

- Dataset macro storico reale ampio;
- provider esterni FRED/ALFRED;
- diagnostica visuale avanzata o export JSON del report;
- editing/upload configurazioni da UI;
- database locale.

## Valutazione

Fase B completata. Il sistema ora ha una diagnostica esplicita per import e configurazioni, una superficie Web read-only per ispezionarla e un percorso batch locale per popolare lo storico con piu' as-of date usando file JSON convenzionali.

La prossima fase consigliata e' la Fase C: decisione sulla persistenza locale e ADR dedicata.
