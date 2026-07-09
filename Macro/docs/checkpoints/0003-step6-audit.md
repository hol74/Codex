# Macro-Regime audit dopo Step 6

Data: 2026-07-02

## Scopo

Questo documento verifica il lavoro svolto nello Step 6 prima di procedere oltre.

Le domande di controllo sono:

- quanto fatto e' coerente con il piano?
- la persistenza e il reporting introdotti rispettano i confini architetturali?
- lo Step 6 e' completo o solo completato come prima tranche?
- abbiamo lasciato indietro qualcosa di necessario?
- abbiamo anticipato elementi che dovevano restare successivi?

## Fonti verificate

Sono stati verificati:

- `macro_regime_plan.step1_done.md`
- `macro_regime_delivery_plan.md`
- `docs/adr/0002-dipendenze-layer.md`
- `docs/domain/prototype_mapping.md`
- `docs/testing/macro_regime_test_plan.md`
- solution `MacroRegime.slnx`
- progetti in `src/`
- progetti in `tests/`
- build e test dell'intera solution
- controlli `rg` sulle dipendenze vietate

## Verdetto sintetico

Lo Step 6 e' stato implementato correttamente come prima tranche minima di persistenza e reporting.

Sono stati introdotti:

- `MacroRegime.Infrastructure`;
- `MacroRegime.Reporting`;
- `MacroRegime.Infrastructure.Tests`;
- `MacroRegime.Reporting.Tests`;
- una porta applicativa per salvare un run;
- un adapter Infrastructure su file JSON;
- un mapper da `RegimeSnapshot` a record persistibile;
- un renderer markdown del report.

Il lavoro e' coerente con le regole di dipendenza:

- `Domain` resta puro;
- `Application` non dipende da `Infrastructure`;
- `Application` espone una porta, non scrive file direttamente;
- `Infrastructure` implementa la porta e usa file system/JSON;
- `Reporting` legge il dominio e produce markdown;
- nessuna UI e' stata introdotta.

Il punto importante: non tutto lo Step 6 esteso e' completo. E' completa la tranche "persistenza/reporting minimale". Restano fuori, correttamente, import reali, EF Core, report salvato come file da servizio dedicato e UI.

## Cosa prevedeva Step 6

Il piano indicava:

- introdurre `MacroRegime.Infrastructure`;
- mappare snapshot e run persistenti;
- recuperare import/as-of dal prototipo Finance;
- introdurre `MacroRegime.Reporting`;
- generare report markdown;
- valutare UI Web.

## Cosa e' stato fatto

### Infrastructure

Creato progetto:

```text
src/MacroRegime.Infrastructure/
```

File principali:

- `Persistence/RegimeRunRecord.cs`
- `Persistence/RegimeRunRecordMapper.cs`
- `Persistence/JsonRegimeRunStore.cs`

Responsabilita' introdotte:

- rappresentare un record persistibile di un `RegimeSnapshot`;
- mappare snapshot di dominio in record Infrastructure;
- salvare il record come JSON su file;
- determinare path deterministico del run:

```text
regime-run-{yyyy-MM-dd}.json
```

### Application

Aggiunta porta:

```text
IRegimeRunStore
```

Aggiornato `CalculateRegimeUseCase`:

- continua a calcolare tramite provider applicativi e detector di dominio;
- puo' salvare il risultato se viene fornito un `IRegimeRunStore`;
- non conosce `JsonRegimeRunStore`;
- non conosce file system;
- non conosce database.

Questa scelta e' coerente con il principio:

```text
Application orchestra, Infrastructure implementa.
```

### Reporting

Creato progetto:

```text
src/MacroRegime.Reporting/
```

File principale:

- `Markdown/MarkdownRegimeReportRenderer.cs`

Il renderer produce un report markdown con:

- as-of date;
- model version;
- feature set version;
- primary regime;
- operational regime;
- confidence;
- composite score;
- probabilita';
- feature scores;
- explanations;
- warnings.

### Test

Aggiunti:

- `MacroRegime.Infrastructure.Tests`
- `MacroRegime.Reporting.Tests`

Copertura introdotta:

- mapping `RegimeSnapshot` -> `RegimeRunRecord`;
- scrittura JSON su directory temporanea;
- generazione markdown leggibile;
- use case Application che salva tramite porta fake.

## Completezza rispetto al piano

| Voce Step 6 | Stato | Nota |
|---|---|---|
| Introdurre `MacroRegime.Infrastructure` | Fatto | Progetto creato e aggiunto alla solution |
| Mappare snapshot e run persistenti | Fatto in forma minima | `RegimeRunRecordMapper` e `RegimeRunRecord` |
| Salvare run | Fatto in forma minima | JSON file store, non database |
| Recuperare import/as-of dal prototipo Finance | Non fatto | Da lasciare a step successivo |
| Introdurre `MacroRegime.Reporting` | Fatto | Progetto creato e aggiunto alla solution |
| Generare report markdown | Fatto come rendering stringa | Non ancora servizio che salva file report |
| Valutare UI Web | Non fatto | Correttamente non anticipato |

Conclusione: Step 6 e' completo come primo incremento tecnico, ma non come intero blocco futuro di persistenza/import/reporting/UI.

## Cose non anticipate

Non risultano introdotti:

- EF Core;
- SQLite;
- DbContext;
- repository database;
- migration;
- import FRED/ALFRED;
- HTTP client;
- Web project;
- controller;
- Razor;
- dashboard;
- allocation engine;
- persistenza dentro `Domain`;
- persistenza diretta dentro `Application`.

Questo e' corretto. La scelta JSON e' volutamente minimale e auditabile.

## Verifiche eseguite

Build:

```text
dotnet build MacroRegime.slnx --no-restore
Avvisi: 0
Errori: 0
```

Test:

```text
dotnet test MacroRegime.slnx --no-restore
Domain.Tests: 71/71
Application.Tests: 6/6
Reporting.Tests: 1/1
Infrastructure.Tests: 2/2
Totale: 80/80
```

Controlli architetturali:

```text
rg "EntityFramework|AspNetCore|DbContext|DbSet|HttpClient|Sqlite|SqlConnection|DateTime\.Now|DateTimeOffset\.Now" src/MacroRegime.Domain src/MacroRegime.Application
```

Risultato:

- nessun match.

```text
rg "MacroRegime.Infrastructure|MacroRegime.Reporting|File\.|Directory\.|Path\." src/MacroRegime.Domain src/MacroRegime.Application
```

Risultato:

- nessun match.

```text
rg "ProjectReference Include=.*MacroRegime.Infrastructure|ProjectReference Include=.*MacroRegime.Reporting" src/MacroRegime.Domain src/MacroRegime.Application tests/MacroRegime.Domain.Tests tests/MacroRegime.Application.Tests --glob "*.csproj"
```

Risultato:

- nessun match.

## Valutazione architetturale

### Domain

Stato: corretto.

Non e' stato modificato per conoscere persistenza, reportistica o file system.

### Application

Stato: corretto.

L'aggiunta di `IRegimeRunStore` e' accettabile perche':

- e' una porta;
- non contiene dettagli tecnici;
- non forza persistenza obbligatoria;
- non crea dipendenza verso Infrastructure.

Rischio da monitorare:

- il use case ora ha due responsabilita': calcolo e salvataggio opzionale. Per ora e' accettabile; se cresceranno audit trail, report e transazioni, conviene separare un orchestratore o una pipeline applicativa.

### Infrastructure

Stato: corretto per incremento minimo.

`JsonRegimeRunStore` usa file system, ma solo nel progetto Infrastructure. Questo rispetta ADR 0002.

Limite:

- non e' ancora persistenza robusta;
- non c'e' idempotenza formalizzata oltre al path deterministico per as-of date;
- non c'e' schema version del record persistito.

### Reporting

Stato: corretto per incremento minimo.

Il renderer markdown non dipende da Infrastructure e non salva file. Produce contenuto leggibile a partire da `RegimeSnapshot`.

Limite:

- non esiste ancora un servizio di report generation che combini renderer e storage;
- non c'e' confronto con periodo precedente;
- non c'e' report di proposta allocativa.

## Lacune da chiudere

### Alta priorita'

1. Introdurre uno schema/versione per `RegimeRunRecord`.
2. Testare idempotenza dello store JSON su stesso as-of date.
3. Aggiungere un servizio applicativo o reporting per generare e salvare report markdown.
4. Definire se il salvataggio run deve avvenire sempre nel use case o in una pipeline separata.

### Media priorita'

1. Aggiungere fixture end-to-end: provider in memoria -> use case -> JSON store -> markdown report.
2. Recuperare dal prototipo Finance i casi as-of/vintage piu' importanti.
3. Definire una `DataCard` per i dati usati nello snapshot persistito.
4. Rendere piu' esplicito il contratto del record persistito.

### Da rimandare

1. EF Core e database.
2. Import FRED/ALFRED.
3. UI Web.
4. Report HTML.
5. Allocation engine.

## Decisione proposta

Si puo' considerare chiusa la prima tranche dello Step 6.

Prima di aprire una fase piu' ambiziosa su database/import/UI, conviene fare un piccolo hardening:

1. idempotenza JSON store;
2. record schema version;
3. generazione report markdown salvata come file;
4. test end-to-end senza rete e senza database.

Questa sequenza mantiene il progetto governabile e impedisce di ricreare il problema del prototipo Finance, dove calcolo, persistenza e presentazione erano troppo vicini.
