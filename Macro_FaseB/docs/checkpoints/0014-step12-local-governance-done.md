# Macro Regime - Step 12 Local Governance Done

Data: 2026-07-06

## Obiettivo

Chiudere i rischi pre-UI individuati nello Step 11 senza introdurre database o UI.

Deliverable previsti:

- tracciamento origine dati;
- modalita' CLI strict per import JSON;
- input summary nel report;
- test diretto della CLI;
- verifica dei gate architetturali.

## Fatto

### Origine dati

Sono stati aggiunti in Application:

- `DataSnapshotSourceKind`;
- `DataSnapshotSourceInfo`;
- `IDataSnapshotSourceInfoProvider`.

`CalculateRegimeUseCase` ora propaga `DataSnapshotSourceInfo` nel risultato di calcolo.

`RunRegimeAnalysisUseCase` porta la stessa informazione fino al report e al risultato finale.

Origini previste:

- `Imported`;
- `Demo`;
- `DemoFallback`;
- `EmptyFallback`;
- `Unspecified`.

### Import JSON e fallback

`JsonDataSnapshotProvider` ora espone `LastSourceInfo` e distingue:

- file import usato davvero;
- fallback demo per file mancante;
- fallback demo per as-of date non coerente;
- fallback vuoto quando non esiste fallback provider.

Il fallback demo non e' piu' invisibile: viene propagato fino al report.

### Strict data

La CLI supporta:

```powershell
--strict-data
```

Comportamento:

- `--strict-data` richiede `--data`;
- se il file non esiste, la run fallisce;
- se il file esiste ma contiene una `asOfDate` diversa da quella richiesta, la run fallisce;
- se il file e' valido e coerente, la run procede con `Data source: Imported`.

### Report

`MarkdownRegimeReportRenderer` include una nuova sezione:

```markdown
## Input Summary
```

La sezione mostra:

- data source;
- dettaglio origine;
- riferimento origine, se disponibile;
- numero di feature attive;
- numero di feature score prodotti;
- numero di warning.

### Test CLI

Aggiunto il progetto:

- `tests/MacroRegime.Cli.Tests`.

Copertura minima:

- CLI demo run scrive run JSON e report markdown;
- `--strict-data` senza `--data` restituisce errore di uso;
- `--strict-data` con file mancante restituisce failure operativa.

## Verifiche

Comandi eseguiti:

```powershell
dotnet restore MacroRegime.slnx
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore
dotnet run --project src\MacroRegime.Cli\MacroRegime.Cli.csproj --no-restore -- --as-of 2026-07-01 --data samples\macro-data-2026-07-01.json --strict-data --output-dir .\.tmp\step12-smoke
```

Risultati:

- restore: superata con accesso NuGet per il nuovo progetto test CLI;
- build: superata, 0 warning, 0 errori;
- test: superati 115/115;
- smoke CLI strict: superato;
- output CLI: `Data source: Imported`;
- report smoke: contiene `## Input Summary`, `Data source: Imported`, `Feature scores produced: 5`, `Decision suggestion: PartialRebalance`.

La cartella temporanea `.tmp\step12-smoke` e' stata rimossa.

## Gate architetturali

Controlli eseguiti:

```powershell
rg -n "EntityFramework|AspNetCore|DbContext|DbSet|HttpClient|Sqlite|SqlConnection|DateTime\.Now|DateTimeOffset\.Now" src\MacroRegime.Domain src\MacroRegime.Application --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "MacroRegime.Infrastructure|MacroRegime.Reporting|File\.|Directory\.|Path\." src\MacroRegime.Domain src\MacroRegime.Application --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "ProjectReference Include=.*MacroRegime.Infrastructure|ProjectReference Include=.*MacroRegime.Reporting" src\MacroRegime.Domain src\MacroRegime.Application tests\MacroRegime.Domain.Tests tests\MacroRegime.Application.Tests --glob '*.csproj'
rg -n "HttpClient|WebRequest|Sqlite|SqlConnection|DbContext|DbSet|EntityFramework" src tests --glob '!**/bin/**' --glob '!**/obj/**'
```

Risultati:

- nessuna violazione Domain/Application;
- nessuna dipendenza vietata;
- nessun uso runtime di database, EF o HTTP.

## Non fatto

Restano volutamente fuori da questo step:

- model version da JSON;
- feature set da JSON;
- policy, portfolio e tilt rules da JSON;
- UI;
- database.

Queste parti possono essere affrontate dopo la UI minima o come step di configurazione locale piu' ampio, se la UI dovra' essere piu' operativa che dimostrativa.

## Decisione

La pipeline locale e' ora piu' governabile:

- non confonde import reale e fallback demo;
- puo' fallire in modo esplicito con `--strict-data`;
- il report dichiara l'origine del dato;
- la CLI ha un contratto testato.

Prossimo passo consigliato:

- Step 13: UI minima sobria su run/report gia' prodotti, mostrando chiaramente data source, warning, regime, probabilita', feature score e allocation proposal.

Alternativa:

- Step 12b: configurare da JSON anche model/feature set/policy/portfolio prima della UI, se vogliamo una prima UI meno demo e piu' operativa.
