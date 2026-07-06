# Macro Regime - Step 12b Local Config Done

Data: 2026-07-06

## Obiettivo

Completare la fase locale pre-UI rendendo configurabili da JSON anche:

- model version;
- feature set;
- strategic allocation policy;
- current portfolio;
- regime tilt rules.

Lo step doveva restare senza UI, database, rete o dipendenze runtime esterne.

## Fatto

### Adapter Infrastructure

Sono stati aggiunti record, mapper e provider JSON in `MacroRegime.Infrastructure/Import`.

Nuovi provider:

- `JsonModelVersionProvider`;
- `JsonFeatureSetProvider`;
- `JsonStrategicAllocationPolicyProvider`;
- `JsonCurrentPortfolioProvider`;
- `JsonRegimeTiltRuleProvider`.

Supporto comune:

- `JsonConfigurationRecords`;
- `JsonConfigurationRecordMapper`;
- `JsonConfigurationFileReader`.

Ogni file JSON dichiara `schemaVersion`.

La versione supportata e' `1`.

### Validazione

Il mapping valida al bordo Infrastructure:

- schema version;
- campi obbligatori;
- enum non supportati;
- date obbligatorie;
- coerenza `asOfDate` del current portfolio;
- vincoli gia' presenti nei value object di dominio.

In caso di JSON invalido o schema non supportato la run fallisce con `InvalidDataException`.

### Fallback demo e strict config

Il comportamento resta coerente con lo Step 12:

- senza file configurazione, la CLI usa i provider demo deterministici;
- con file configurazione assente e `--strict-config` non attivo, il provider usa il fallback demo;
- con file configurazione assente e `--strict-config`, la run fallisce;
- per model version, `effectiveFrom` deve essere minore o uguale alla `as-of date`;
- per current portfolio, `asOfDate` deve coincidere con la `as-of date`.

### CLI

La CLI supporta nuovi flag:

```powershell
--model path
--feature-set path
--policy path
--portfolio path
--tilts path
--strict-config
```

Il default resta retrocompatibile: una run con solo `--as-of` continua a funzionare con data/config demo.

### Sample JSON

Aggiunti sample locali eseguibili:

- `samples/model-version-baseline.json`;
- `samples/feature-set-baseline.json`;
- `samples/allocation-policy-balanced.json`;
- `samples/current-portfolio-2026-07-01.json`;
- `samples/regime-tilt-rules.json`.

I sample sono compatibili con `samples/macro-data-2026-07-01.json` e alimentano una run completa.

## Test

Aggiunto:

- `tests/MacroRegime.Infrastructure.Tests/Import/JsonConfigurationProviderTests.cs`.

Copertura:

- lettura dei cinque provider JSON;
- rifiuto schema version non supportata;
- fallback portfolio quando la data non coincide;
- errore strict portfolio quando la data non coincide;
- pipeline end-to-end locale con data JSON e configurazioni JSON.

Aggiornato:

- `tests/MacroRegime.Cli.Tests/MacroRegimeCliTests.cs`.

Copertura aggiunta:

- `--strict-config` con file configurazione mancante restituisce failure operativa.

## Verifiche

Comandi eseguiti:

```powershell
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore
dotnet run --project src\MacroRegime.Cli\MacroRegime.Cli.csproj --no-restore -- --as-of 2026-07-01 --data samples\macro-data-2026-07-01.json --strict-data --model samples\model-version-baseline.json --feature-set samples\feature-set-baseline.json --policy samples\allocation-policy-balanced.json --portfolio samples\current-portfolio-2026-07-01.json --tilts samples\regime-tilt-rules.json --strict-config --output-dir .\.tmp\step12b-smoke
```

Risultati:

- build: superata, 0 warning, 0 errori;
- test: superati 121/121;
- smoke CLI: superato;
- primary regime: `Goldilocks`;
- operational regime: `Goldilocks`;
- data source: `Imported`;
- allocation suggestion: `PartialRebalance`;
- model nel report: `CRS Rule-Based Engine v0.1-local`;
- feature set nel report: `CRS Baseline v0.1-local`.

La cartella temporanea `.tmp\step12b-smoke` e' stata rimossa.

## Gate architetturali

Comandi eseguiti:

```powershell
rg -n "EntityFramework|AspNetCore|DbContext|DbSet|HttpClient|Sqlite|SqlConnection|DateTime\.Now|DateTimeOffset\.Now" src\MacroRegime.Domain src\MacroRegime.Application --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "MacroRegime.Infrastructure|MacroRegime.Reporting|File\.|Directory\.|Path\." src\MacroRegime.Domain src\MacroRegime.Application --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "ProjectReference Include=.*MacroRegime.Infrastructure|ProjectReference Include=.*MacroRegime.Reporting" src\MacroRegime.Domain src\MacroRegime.Application tests\MacroRegime.Domain.Tests tests\MacroRegime.Application.Tests --glob '*.csproj'
rg -n "HttpClient|WebRequest|Sqlite|SqlConnection|DbContext|DbSet|EntityFramework" src tests --glob '!**/bin/**' --glob '!**/obj/**'
```

Risultato:

- nessuna violazione trovata;
- Domain e Application restano senza dipendenze da Infrastructure/Reporting;
- nessun database, EF, HTTP o rete introdotti;
- filesystem confinato a Infrastructure/CLI/test.

## Non fatto

Restano fuori dallo Step 12b:

- UI;
- database;
- import storico di serie reali;
- composizione tramite dependency injection container;
- metadati/report espliciti sull'origine delle configurazioni, oltre a model/versione feature gia' presenti nel report;
- validazione formale JSON Schema esterna.

## Decisione

Lo Step 12b chiude il prerequisito per una UI meno dimostrativa: la pipeline puo' ora essere alimentata da file locali versionati per dati, modello, feature set, policy, portafoglio e tilt.

Prossimo passo consigliato:

- Step 13: UI minima read-only sopra run/report locali, senza database, mostrando chiaramente as-of date, data source, regime, probabilita', feature score, warning e allocation proposal.

Alternativa, se vogliamo restare ancora nel backend:

- aggiungere un manifest di configurazione unico che punti ai sei file JSON e renda piu' semplice l'avvio CLI.
