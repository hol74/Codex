# Macro Regime - Step 8 Demo Adapters Done

Data: 2026-07-02

## Obiettivo

Introdurre adapter Infrastructure demo deterministici per alimentare la pipeline fuori dai test e ridurre una parte della duplicazione fixture emersa nell'audit di Step 7.

## Fatto

Sono stati aggiunti provider demo in `MacroRegime.Infrastructure.Demo`:

- `DemoDataSnapshotProvider`;
- `DemoModelVersionProvider`;
- `DemoFeatureSetProvider`;
- `DemoStrategicAllocationPolicyProvider`;
- `DemoCurrentPortfolioProvider`;
- `DemoRegimeTiltRuleProvider`;
- `DemoMacroRegimeInputs`.

I provider implementano le porte Application esistenti e ritornano input deterministici:

- scenario macro Goldilocks;
- modello baseline demo;
- feature set baseline demo;
- policy bilanciata demo;
- portafoglio corrente demo;
- tilt rule per Goldilocks e RecessionStress.

Non sono stati introdotti:

- database;
- rete;
- EF;
- UI;
- clock impliciti.

## Test aggiunti o aggiornati

Aggiunti test Infrastructure dedicati:

- verifica che i provider demo restituiscano input deterministici;
- verifica che i provider demo alimentino `RunRegimeAnalysisUseCase` end-to-end con store JSON locale e report markdown locale.

Aggiornato l'E2E Infrastructure:

- `RunRegimeAnalysis_UsesOnlyLocalFileAdapters` usa ora provider demo reali invece di fake provider privati;
- rimossa la duplicazione locale di data snapshot, model version, feature set version, policy, portfolio e tilt rule da quel test.

Pulizia fixture Application:

- i test `RunRegimeAnalysisUseCaseTests` riusano `AllocationProposalTestFixtures` per policy, portafoglio e tilt rule.

## Verifiche

Comandi eseguiti:

```powershell
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore
rg -n "EntityFramework|AspNetCore|DbContext|DbSet|HttpClient|Sqlite|SqlConnection|DateTime\.Now|DateTimeOffset\.Now" src\MacroRegime.Domain src\MacroRegime.Application --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "MacroRegime.Infrastructure|MacroRegime.Reporting|File\.|Directory\.|Path\." src\MacroRegime.Domain src\MacroRegime.Application --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "ProjectReference Include=.*MacroRegime.Infrastructure|ProjectReference Include=.*MacroRegime.Reporting" src\MacroRegime.Domain src\MacroRegime.Application tests\MacroRegime.Domain.Tests tests\MacroRegime.Application.Tests --glob '*.csproj'
rg -n "HttpClient|WebRequest|Sqlite|SqlConnection|DbContext|DbSet|EntityFramework" src tests --glob '!**/bin/**' --glob '!**/obj/**'
```

Risultati:

- build: superata, 0 warning, 0 errori;
- test: superati 105/105;
- gate Domain/Application: nessuna violazione;
- gate rete/database: nessuna violazione;
- gate riferimenti progetto: nessuna dipendenza vietata.

## Stato fixture

La duplicazione fixture e' stata ridotta dove impattava la vertical slice Infrastructure.
Restano duplicazioni locali accettabili nei test Domain, Reporting e in alcune factory Application per snapshot/model/feature set.

Decisione: non introdurre ancora un progetto `MacroRegime.Testing`. Se il prossimo incremento data/import aumenta gli scenari, allora conviene creare builder test piu' formali:

- `RegimeSnapshotTestBuilder`;
- `RegimeInputTestBuilder`;
- `AllocationProposalTestBuilder`;
- `AllocationPolicyTestBuilder`.

## Prossimo passo consigliato

Passare a data/import locale, ancora senza database:

- definire record di input importabile;
- implementare un file adapter deterministico per `IDataSnapshotProvider`;
- validare schema/versione del file importato;
- mantenere i provider demo come fallback o scenario smoke test.
