# Macro-Regime plan: verifica fino allo Step 6

Data: 2026-07-02

## Scopo

Questo documento ripercorre il piano originale del progetto Macro-Regime, verifica lo stato effettivo del lavoro fino allo Step 6 e separa tre cose che non devono essere confuse:

- cio' che e' stato completato;
- cio' che e' stato correttamente rimandato;
- cio' che appartiene a piani precedenti o piu' ampi e non e' ancora parte dello scheletro corrente.

Il risultato e' un checkpoint operativo prima di aprire nuove fasi.

## Fonti considerate

Documenti principali:

- `macro_regime_plan.md`
- `macro_regime_delivery_plan.md`
- `macro_regime_architectural_restart_plan.md`
- `macro_regime_plan.step1_done.md`
- `macro_regime_step4_audit.md`
- `macro_regime_step6_audit.md`
- `docs/adr/0001-restart-architetturale.md`
- `docs/adr/0002-dipendenze-layer.md`
- `docs/domain/domain_core_design.md`
- `docs/testing/macro_regime_test_plan.md`

Artefatti tecnici verificati:

- `MacroRegime.slnx`
- `src/MacroRegime.Domain`
- `src/MacroRegime.Application`
- `src/MacroRegime.Infrastructure`
- `src/MacroRegime.Reporting`
- `tests/MacroRegime.Domain.Tests`
- `tests/MacroRegime.Application.Tests`
- `tests/MacroRegime.Infrastructure.Tests`
- `tests/MacroRegime.Reporting.Tests`

## Verdetto sintetico

Il piano operativo fino allo Step 6 e' completato nel perimetro corretto del restart architetturale.

Sono completi:

- documentazione minima di governance e restart;
- solution C# modulare;
- core di dominio puro;
- tipi principali di dominio;
- servizi di dominio base;
- baseline rule-based detector v0.1;
- application layer minimale con porte;
- persistenza JSON minimale;
- record persistito con schema version;
- idempotenza dello store JSON su stesso as-of date;
- reporting markdown;
- servizio applicativo per generare e salvare report;
- test end-to-end locale senza rete e senza database.

Non e' completa la Fase 6 estesa del primissimo piano, se interpretata come applicazione completa con EF Core, seed database, controller MVC e UI. Questa differenza e' intenzionale: dopo il post-mortem del prototipo Finance abbiamo scelto un restart piu' disciplinato, con Infrastructure e Reporting introdotti solo come adapter minimi dopo il core stabile.

## Lettura corretta dello Step 6

Nel documento `macro_regime_plan.md`, la "Fase 6 - Implementazione applicativa" includeva data foundation, feature store, baseline, UI e report. Quel piano era precedente al post-mortem e alla decisione di restart.

Nel piano di restart, lo Step 6 e' stato ridefinito come primo ingresso controllato di persistenza e reporting dopo Domain e Application stabili:

- introdurre `MacroRegime.Infrastructure`;
- mappare snapshot e run persistenti;
- introdurre `MacroRegime.Reporting`;
- generare report markdown;
- rimandare database, import reali e UI fino a quando il core non fosse stato verificato.

La verifica di questo documento usa quindi il piano operativo approvato dopo il restart, non il primo tentativo applicativo piu' largo.

## Stato per step

| Step | Obiettivo | Stato | Evidenza |
|---|---|---|---|
| 0 | Governance, post-mortem, restart plan, ADR e documenti minimi | Completato | `macro_regime_governance.md`, `macro_regime_delivery_plan.md`, `macro_regime_postmortem.md`, ADR e documenti `docs/` |
| 1 | Solution C# minimale, Domain, Application, Domain.Tests, primi value object | Completato | `macro_regime_plan.step1_done.md`; value object in `Common/` e `Time/`; test puri |
| 2 | Tipi di dominio principali | Completato | `RegimeType`, `EconomicDimension`, `FeaturePolarity`, `ModelRole`, `RegimeProbability`, `FeatureDefinition`, `FeatureScore`, `FeatureSetVersion`, `ModelVersion`, `RegimeExplanation`, `RegimeSnapshot` |
| 3 | Servizi di dominio base | Completato | `RegimeProbabilityNormalizer`, `CompositeScoreCalculator`, `RegimeExplanationBuilder` e test relativi |
| 4 | Baseline rule-based detector v0.1 e data snapshot | Completato | `FeatureNormalizer`, `BaselineRegimeDetector`, `BaselineRegimeParameters`, `DataSnapshot`; audit in `macro_regime_step4_audit.md` |
| 5 | Application layer minimale | Completato | `CalculateRegimeUseCase`, command/result, porte per data snapshot, model version, feature set e run store |
| 6 | Persistenza e reporting minimi | Completato come tranche core | `MacroRegime.Infrastructure`, `MacroRegime.Reporting`, JSON store, record schema version, report markdown, report store, end-to-end locale |

## Dettaglio Step 1

Lo Step 1 ha creato lo scheletro tecnico iniziale:

- `MacroRegime.slnx`;
- `MacroRegime.Domain`;
- `MacroRegime.Application`;
- `MacroRegime.Domain.Tests`.

Sono stati implementati value object puri:

- `Probability`;
- `RegimeConfidence`;
- `FeatureWeight`;
- `NormalizedScore`;
- `AsOfDate`;
- `ObservationDate`;
- `PublicationDate`;
- `AvailabilityDate`.

Valutazione: completato. Il dominio e' nato senza EF, web, database o file system.

## Dettaglio Step 2

Lo Step 2 ha introdotto il vocabolario principale del dominio:

- regimi;
- dimensioni economiche;
- polarita' feature;
- ruolo dei modelli;
- probabilita' di regime;
- definizioni e score delle feature;
- versioni di feature set e modello;
- spiegazioni;
- snapshot di regime.

I test coprono le invarianti richieste:

- probabilita' e rank validi;
- codice/nome feature obbligatori;
- input incoerenti dei feature score rifiutati;
- snapshot con as-of date, model version e feature set version obbligatori;
- probabilita' ordinate e normalizzate.

Valutazione: completato.

## Dettaglio Step 3

Lo Step 3 ha introdotto servizi di dominio puri:

- `RegimeProbabilityNormalizer`;
- `CompositeScoreCalculator`;
- `RegimeExplanationBuilder`.

I test coprono:

- normalizzazione di distribuzioni grezze;
- fallback uniforme quando la somma e' zero;
- media pesata corretta;
- driver ordinati per impatto;
- prime funzioni per driver e segnali contrari.

Valutazione: completato.

## Dettaglio Step 4

Lo Step 4 ha implementato la baseline rule-based v0.1:

- osservazioni macro e market;
- `DataSnapshot`;
- normalizzazione feature;
- parametri baseline;
- detector baseline;
- mapping verso regimi operativi;
- gestione di `UncertainTransition`;
- warnings per input mancanti o non disponibili.

La verifica e' documentata in `macro_regime_step4_audit.md`.

Valutazione: completato per il baseline core. Non sono stati introdotti modelli avanzati, coerentemente con la governance.

## Dettaglio Step 5

Lo Step 5 ha introdotto l'application layer minimo:

- `CalculateRegimeCommand`;
- `CalculateRegimeUseCase`;
- `CalculateRegimeResult`;
- `IDataSnapshotProvider`;
- `IModelVersionProvider`;
- `IFeatureSetProvider`;
- `IRegimeRunStore`.

Il use case orchestra i provider e il detector, ma non conosce file system, database, HTTP o Infrastructure.

Valutazione: completato.

## Dettaglio Step 6

Lo Step 6 ha introdotto persistenza e reporting come adapter, non come nuovo centro della logica.

Infrastructure:

- `RegimeRunRecord`;
- `RegimeRunRecordMapper`;
- `JsonRegimeRunStore`;
- `FileRegimeReportStore`.

Reporting:

- `MarkdownRegimeReportRenderer`.

Application report flow:

- `GenerateRegimeReportCommand`;
- `GenerateRegimeReportUseCase`;
- `GenerateRegimeReportResult`;
- `IRegimeReportRenderer`;
- `IRegimeReportStore`.

Hardening completato dopo il precedente audit Step 6:

- `RegimeRunRecord` include `SchemaVersion`;
- lo store JSON usa path deterministico `regime-run-{yyyy-MM-dd}.json`;
- l'idempotenza sullo stesso snapshot/as-of date e' testata;
- il report markdown viene generato e salvato su file;
- esiste un test end-to-end locale: snapshot -> JSON run -> markdown report;
- il test end-to-end non usa rete, database o servizi esterni.

Valutazione: completato come Step 6 core.

## Verifiche tecniche eseguite

Build:

```text
dotnet build MacroRegime.slnx --no-restore
Risultato: completata
Warning: 0
Errori: 0
```

Test:

```text
dotnet test MacroRegime.slnx --no-restore
Domain.Tests: 71/71
Application.Tests: 7/7
Reporting.Tests: 1/1
Infrastructure.Tests: 5/5
Totale: 84/84
```

Gate architetturali:

```text
rg "EntityFramework|AspNetCore|DbContext|DbSet|HttpClient|Sqlite|SqlConnection|DateTime\.Now|DateTimeOffset\.Now" src/MacroRegime.Domain src/MacroRegime.Application
Risultato: nessun match
```

```text
rg "MacroRegime.Infrastructure|MacroRegime.Reporting|File\.|Directory\.|Path\." src/MacroRegime.Domain src/MacroRegime.Application
Risultato: nessun match
```

```text
rg "ProjectReference Include=.*MacroRegime.Infrastructure|ProjectReference Include=.*MacroRegime.Reporting" src/MacroRegime.Domain src/MacroRegime.Application tests/MacroRegime.Domain.Tests tests/MacroRegime.Application.Tests --glob "*.csproj"
Risultato: nessun match
```

```text
rg "HttpClient|WebRequest|Sqlite|SqlConnection|DbContext|DbSet|EntityFramework" src tests
Risultato: nessun match
```

## Cosa non e' stato anticipato

Non risultano introdotti:

- EF Core;
- SQLite;
- DbContext;
- migration;
- HTTP client;
- import FRED/ALFRED;
- import live;
- Web project;
- controller MVC;
- Razor view;
- dashboard;
- allocation engine;
- research lab Python;
- HMM o clustering;
- ottimizzazione di portafoglio;
- logica di regime dentro Infrastructure o Web.

Questo e' corretto rispetto al restart: il sistema resta piccolo, testabile e governabile.

## Cosa manca ancora

Mancano ancora elementi importanti, ma appartengono agli step successivi o al completamento della prima release informativa:

- import/as-of adapter recuperati dal prototipo Finance;
- scelta di persistenza robusta oltre JSON;
- eventuale EF Core/database dopo contratto stabile;
- model card e data card piu' formali;
- report con confronto periodo precedente;
- report con proposta allocativa;
- allocation proposal vincolata;
- UI minima o dashboard;
- research lab per challenger model;
- stress test e walk-forward;
- promozione controllata di eventuali modelli avanzati.

## Rischi residui

| Rischio | Stato | Contromisura |
|---|---|---|
| Lo Step 6 venga confuso con la vecchia Fase 6 applicativa completa | Aperto | Usare questo documento come baseline: Step 6 core completato, UI/database rimandati |
| JSON store diventi persistenza definitiva senza schema evolution | Da monitorare | Mantenere `SchemaVersion` e introdurre migrazione/compatibilita' prima di dati reali |
| Reporting cresca fino a contenere logica di dominio | Da monitorare | Reporting deve formattare, non calcolare |
| Application use case accumuli troppe responsabilita' | Da monitorare | Separare pipeline/orchestratore se calcolo, persistenza, report e audit crescono |
| Mancanza di allocation proposal | Non ancora affrontato | Prossimo blocco funzionale dopo hardening di report/persistenza |

## Decisione

Possiamo considerare completato il piano operativo fino allo Step 6.

La formula corretta e':

```text
Step 1-6 completati per il restart architetturale core.
La prima release informativa completa non e' ancora conclusa.
```

Il prossimo lavoro non dovrebbe tornare a rifare il core. Dovrebbe invece scegliere una delle due direzioni:

1. chiudere il blocco allocation proposal vincolata;
2. rafforzare data/import/as-of persistence prima di introdurre UI.

La direzione piu' prudente e' allocation proposal vincolata solo se resta puramente di dominio/applicazione e non richiede ancora database o UI. In alternativa, il prossimo passo tecnico e' recuperare dal prototipo Finance gli adapter as-of/import piu' utili, mantenendoli in Infrastructure.
