# Macro Regime - Step 12 Closed Checkpoint

Data: 2026-07-06

## Decisione

Lo Step 12 e' completato.

Per chiarezza, lo Step 12 risulta composto da due incrementi:

- Step 12: local governance prima della UI;
- Step 12b: local JSON configuration prima della UI.

Il secondo incremento ha chiuso l'alternativa lasciata aperta dal checkpoint Step 12: evitare che la prima UI fosse ancora troppo demo-hardcoded.

## Scope verificato

Documenti letti:

- `macro_regime_plan.md`;
- `macro_regime_plan.step11_pre_ui_audit.md`;
- `macro_regime_plan.step12_local_governance_done.md`;
- `macro_regime_plan.step12b_local_config_done.md`.

Codice verificato:

- Application results/report command con `DataSnapshotSourceInfo`;
- provider demo/import dati;
- provider JSON per model, feature set, policy, portfolio e tilt;
- CLI composition root;
- renderer markdown;
- test CLI, Infrastructure, Reporting e pipeline end-to-end.

## Criteri Step 12

### Richiesti dallo Step 11

- tracciamento origine dati;
- `--strict-data`;
- input summary nel report;
- test diretto della CLI;
- gate architetturali.

Esito: completati.

### Estensione Step 12b

- model version da JSON;
- feature set da JSON;
- strategic allocation policy da JSON;
- current portfolio da JSON;
- regime tilt rules da JSON;
- `--strict-config`;
- sample JSON locali;
- test end-to-end senza rete/database.

Esito: completati.

## Evidenze funzionali

La CLI ora puo' essere eseguita in tre modalita':

1. Demo completa:
   - solo `--as-of`;
   - usa dati e configurazioni demo deterministici.

2. Data import governato:
   - `--data`;
   - opzionale `--strict-data`;
   - report con data source effettiva.

3. Local config completa:
   - `--data`;
   - `--model`;
   - `--feature-set`;
   - `--policy`;
   - `--portfolio`;
   - `--tilts`;
   - `--strict-data`;
   - `--strict-config`.

I sample locali presenti in `samples/` alimentano una run completa.

## Verifiche eseguite

Prima verifica:

```powershell
dotnet build MacroRegime.slnx --no-restore
```

Esito iniziale:

- fallita per asset NuGet incoerenti dopo cambio/restore SDK;
- errore in `ResolvePackageAssets`, non in compilazione C#.

Correzione ambientale:

```powershell
dotnet restore MacroRegime.slnx
```

Nota:

- il restore in sandbox e' fallito sui progetti test per accesso NuGet/repository signatures;
- il restore fuori sandbox e' riuscito.

Verifiche finali:

```powershell
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore
dotnet run --project src\MacroRegime.Cli\MacroRegime.Cli.csproj --no-restore -- --as-of 2026-07-01 --data samples\macro-data-2026-07-01.json --strict-data --model samples\model-version-baseline.json --feature-set samples\feature-set-baseline.json --policy samples\allocation-policy-balanced.json --portfolio samples\current-portfolio-2026-07-01.json --tilts samples\regime-tilt-rules.json --strict-config --output-dir .\.tmp\step12-closure-smoke
```

Risultati:

- restore: superato dopo autorizzazione rete;
- build: superata, 0 warning, 0 errori;
- test: superati 121/121;
- smoke CLI: superato;
- primary regime: `Goldilocks`;
- operational regime: `Goldilocks`;
- data source: `Imported`;
- allocation suggestion: `PartialRebalance`.

La cartella `.tmp\step12-closure-smoke` e' stata rimossa.

## Gate architetturali

Comandi eseguiti:

```powershell
rg -n --glob '!**/bin/**' --glob '!**/obj/**' "EntityFramework|AspNetCore|DbContext|DbSet|HttpClient|Sqlite|SqlConnection|DateTime\.Now|DateTimeOffset\.Now" src\MacroRegime.Domain src\MacroRegime.Application
rg -n --glob '!**/bin/**' --glob '!**/obj/**' "MacroRegime.Infrastructure|MacroRegime.Reporting|File\.|Directory\.|Path\." src\MacroRegime.Domain src\MacroRegime.Application
rg -n --glob '*.csproj' "ProjectReference Include=.*MacroRegime.Infrastructure|ProjectReference Include=.*MacroRegime.Reporting" src\MacroRegime.Domain src\MacroRegime.Application tests\MacroRegime.Domain.Tests tests\MacroRegime.Application.Tests
rg -n --glob '!**/bin/**' --glob '!**/obj/**' "HttpClient|WebRequest|Sqlite|SqlConnection|DbContext|DbSet|EntityFramework" src tests
```

Risultato:

- nessuna violazione trovata;
- Domain e Application restano puliti;
- nessun database;
- nessuna rete runtime;
- filesystem confinato a Infrastructure, CLI e test.

## Stato Git

Il working tree contiene modifiche non committate sia dello Step 12 sia dello Step 12b.

Questo checkpoint non introduce commit; registra solo lo stato tecnico verificato.

## Cosa resta fuori dallo Step 12

Restano volutamente esclusi:

- UI;
- database;
- import storico da provider esterni;
- manifest unico di configurazione;
- JSON Schema formale;
- dependency injection container applicativo generalizzato.

Questi punti non bloccano lo Step 13.

## Conclusione

Possiamo passare allo Step 13.

La prossima fase puo' costruire una UI read-only senza introdurre database, basandosi su:

- run JSON persistite;
- report markdown;
- sample JSON locali;
- CLI/composition root gia' verificata;
- contratti Application gia' presenti.
