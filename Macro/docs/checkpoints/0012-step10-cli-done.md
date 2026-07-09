# Macro Regime - Step 10 CLI Done

Data: 2026-07-02

## Obiettivo

Introdurre una composition root locale prima della UI:

- eseguire la pipeline fuori dai test;
- usare import JSON locale con fallback demo;
- salvare run JSON e report markdown;
- non introdurre database, rete runtime o UI.

## Fatto

E' stato aggiunto il progetto:

- `src/MacroRegime.Cli`.

La CLI compone:

- `JsonDataSnapshotProvider` con fallback `DemoDataSnapshotProvider`, se viene passato `--data`;
- `DemoModelVersionProvider`;
- `DemoFeatureSetProvider`;
- `DemoStrategicAllocationPolicyProvider`;
- `DemoCurrentPortfolioProvider`;
- `DemoRegimeTiltRuleProvider`;
- `JsonRegimeRunStore`;
- `FileRegimeReportStore`;
- `MarkdownRegimeReportRenderer`;
- `RunRegimeAnalysisUseCase`.

La solution include ora `MacroRegime.Cli` sotto `/src/`.

## Uso

Esecuzione con import JSON locale:

```powershell
dotnet run --project src\MacroRegime.Cli\MacroRegime.Cli.csproj -- --as-of 2026-07-01 --data samples\macro-data-2026-07-01.json --output-dir macro-regime-output
```

Esecuzione demo pura:

```powershell
dotnet run --project src\MacroRegime.Cli\MacroRegime.Cli.csproj -- --as-of 2026-07-01 --output-dir macro-regime-output
```

Output atteso:

- `macro-regime-output\runs\regime-run-yyyy-MM-dd.json`;
- `macro-regime-output\reports\macro-regime-report-yyyy-MM-dd.md`.

## Sample import

E' stato aggiunto:

- `samples/macro-data-2026-07-01.json`.

Il sample usa schema import v1 e alimenta uno scenario Goldilocks coerente con i provider demo.

## Verifiche

Comandi eseguiti:

```powershell
dotnet restore MacroRegime.slnx
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore
dotnet run --project src\MacroRegime.Cli\MacroRegime.Cli.csproj --no-restore -- --as-of 2026-07-01 --data samples\macro-data-2026-07-01.json --output-dir .\.tmp\cli-smoke
```

Risultati:

- restore: superata dopo accesso NuGet, necessario per i pacchetti test;
- build: superata, 0 warning, 0 errori;
- test: superati 111/111;
- smoke CLI: superato;
- report smoke verificato con `Primary regime: Goldilocks`, `## Allocation Proposal`, `Decision suggestion: PartialRebalance`.

La cartella temporanea `.tmp\cli-smoke` e' stata rimossa dopo la verifica.

## Gate architetturali

Verificati:

- Domain/Application non dipendono da Infrastructure, Reporting, file system, database, web o clock impliciti;
- nessun uso di EF, HTTP o SQL in `src` e `tests`;
- la composizione Infrastructure/Reporting/Application avviene solo nel progetto esterno `MacroRegime.Cli` e nei test.

## Decisione

La pipeline e' ora eseguibile localmente senza UI e senza database.

Il prossimo passo migliore e' un audit breve prima della UI:

- verificare che CLI, import JSON, demo providers e report coprano il flusso minimo desiderato;
- decidere se rendere configurabili anche model/feature set da file;
- solo dopo introdurre una UI minima o un ulteriore adapter dati.
