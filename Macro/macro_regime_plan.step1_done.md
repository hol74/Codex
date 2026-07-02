# Macro-Regime plan: step 1 done

Data: 2026-07-02

## Scopo del documento

Questo documento riassume il lavoro svolto finora sul progetto Macro-Regime, il piano realizzato, i passi completati, le verifiche eseguite e i prossimi passi da compiere.

Il file rappresenta il checkpoint di chiusura dello Step 1: dalla fase di analisi/governance alla creazione dello scheletro C# minimale con primi value object e test puri.

## Obiettivo del progetto

Costruire un Macro-Regime Engine informativo, governato e auditabile per supportare decisioni di asset allocation personale in funzione della probabilita' dei diversi regimi macro/market.

Il sistema non deve essere un modello che decide automaticamente il portafoglio. Deve invece:

- stimare probabilita' di regime;
- spiegare driver e segnali contrari;
- distinguere macro regime, market regime e portfolio regime;
- tradurre il contesto in proposte allocative vincolate;
- rispettare policy strategica, bande, turnover, costi, fiscalita' e liquidita';
- mantenere audit trail e ricostruibilita' as-of date;
- lasciare la decisione finale all'owner umano.

## Piano realizzato

Il lavoro e' stato reimpostato in quattro blocchi.

### 1. Consolidamento della base informativa

Sono stati presi come input i documenti gia' disponibili:

- `macro_regime.md`
- `macro_regime_github.md`
- `macro_regime_plan.md`

Da questi documenti sono emersi principi forti:

- il regime e' probabilistico;
- cash e liquidita' sono asset/rischi espliciti;
- macro regime, market regime e portfolio regime devono restare separati;
- la baseline rule-based deve precedere modelli avanzati;
- HMM, clustering e ML devono entrare come challenger;
- il sistema deve essere ricostruibile as-of date;
- l'allocation deve essere vincolata e spiegabile.

### 2. Governance e delivery plan

Sono stati creati:

- `chat1.md`
- `chat2.md`
- `macro_regime_governance.md`
- `macro_regime_delivery_plan.md`

Questi documenti hanno definito:

- responsabilita' logiche;
- ruolo dell'owner umano;
- ruolo di Codex come esecutore;
- gate di progetto;
- model card;
- data card;
- audit trail minimo;
- milestone;
- Definition of Done;
- ordine di sviluppo.

### 3. Analisi del primo tentativo Finance

E' stato analizzato il codice in:

```text
C:\ProgettiAzure\Codex\Finance\src
```

I cinque progetti analizzati erano:

- `Finance.Domain`
- `Finance.Application`
- `Finance.Infrastructure`
- `Finance.Analytics`
- `Finance.Web`

Il primo tentativo e' risultato tecnicamente utile ma architetturalmente non soddisfacente.

Punti recuperabili:

- tassonomia macro;
- entita' informative;
- gestione as-of/vintage;
- baseline rule-based;
- seed demo;
- dashboard;
- test su vintage/as-of e idempotenza run.

Problema principale:

- il cuore del calcolo viveva in Infrastructure e dipendeva da EF Core.

Decisione:

- usare Finance come reference implementation;
- non proseguire con refactor diretto;
- avviare restart architetturale controllato.

Documento prodotto:

- `macro_regime_postmortem.md`

### 4. Restart architetturale e documenti minimi

Sono stati creati:

- `macro_regime_architectural_restart_plan.md`
- `docs/adr/0001-restart-architetturale.md`
- `docs/adr/0002-dipendenze-layer.md`
- `docs/domain/macro_regime_glossary.md`
- `docs/domain/prototype_mapping.md`
- `docs/domain/domain_core_design.md`
- `docs/testing/macro_regime_test_plan.md`

Questi documenti hanno definito:

- decisione formale di restart;
- regole di dipendenza fra layer;
- glossario di dominio;
- mapping dal prototipo Finance al nuovo sistema;
- design del domain core;
- test plan prima del codice;
- gate prima dello scheletro.

## Passi tecnici completati

### Solution minimale

E' stata generata una solution C# minimale:

```text
MacroRegime.slnx
src/
  MacroRegime.Domain/
  MacroRegime.Application/
tests/
  MacroRegime.Domain.Tests/
```

Progetti creati:

- `src/MacroRegime.Domain/MacroRegime.Domain.csproj`
- `src/MacroRegime.Application/MacroRegime.Application.csproj`
- `tests/MacroRegime.Domain.Tests/MacroRegime.Domain.Tests.csproj`

Dipendenze:

- `MacroRegime.Application` dipende da `MacroRegime.Domain`;
- `MacroRegime.Domain.Tests` dipende da `MacroRegime.Domain`;
- `MacroRegime.Domain` non dipende da altri layer.

### Value object implementati

Sono stati implementati i primi value object puri.

In `src/MacroRegime.Domain/Common/`:

- `Probability`
- `RegimeConfidence`
- `FeatureWeight`
- `NormalizedScore`

In `src/MacroRegime.Domain/Time/`:

- `AsOfDate`
- `ObservationDate`
- `PublicationDate`
- `AvailabilityDate`

Invarianti introdotte:

- probabilita' fra 0 e 1;
- confidence fra 0 e 1;
- peso feature non negativo;
- score normalizzato fra 0 e 1;
- date obbligatorie, non `DateOnly.MinValue`;
- una publication date successiva alla as-of date non e' usabile;
- una availability date successiva alla as-of date non e' usabile.

### Test puri implementati

Sono stati implementati test xUnit puri in:

- `tests/MacroRegime.Domain.Tests/Common/`
- `tests/MacroRegime.Domain.Tests/Time/`

Test coperti:

- `Probability` accetta valori 0..1 e rifiuta valori fuori range;
- `RegimeConfidence` accetta valori 0..1 e rifiuta valori fuori range;
- `FeatureWeight` accetta zero/positivi e rifiuta negativi;
- `NormalizedScore` accetta 0, 0.5, 1 e rifiuta valori fuori range;
- `AsOfDate` rifiuta `DateOnly.MinValue`;
- publication date futura non e' usabile as-of;
- availability date futura non e' usabile as-of;
- date value object rifiutano valori minimi;
- observation date puo' essere confrontata con publication date.

## Verifiche eseguite

### Test

Comando eseguito:

```text
dotnet test MacroRegime.slnx
```

Risultato:

- test passati: 29;
- test falliti: 0;
- test ignorati: 0.

Nota operativa:

- il primo tentativo di `dotnet test` ha fallito il restore xUnit per blocco rete NuGet in sandbox;
- il comando e' stato rilanciato con permesso elevato per consentire il restore;
- dopo il restore, i test sono passati.

### Build

Comando eseguito:

```text
dotnet build MacroRegime.slnx --no-restore
```

Risultato:

- build completata;
- warning: 0;
- errori: 0.

### Verifica architetturale

E' stato controllato che `MacroRegime.Domain` e `MacroRegime.Application` non contengano riferimenti a:

- Entity Framework;
- ASP.NET;
- `DbContext`;
- `DbSet`;
- `HttpClient`.

Risultato:

- nessun riferimento vietato trovato nei sorgenti del Domain/Application.

## Stato attuale

Lo Step 1 e' completato.

Il progetto ha ora:

- governance documentata;
- piano di delivery;
- post-mortem del prototipo;
- decisione di restart;
- ADR minime;
- glossario;
- mapping prototipo;
- domain core design;
- test plan;
- solution C# minimale;
- value object iniziali;
- test puri verdi.

Il nuovo sistema non contiene ancora:

- enum `RegimeType`;
- enum `EconomicDimension`;
- `FeatureDefinition`;
- `FeatureScore`;
- `FeatureSetVersion`;
- `ModelVersion`;
- `RegimeProbability`;
- `RegimeSnapshot`;
- `RegimeExplanation`;
- normalizer;
- probability normalizer;
- composite score calculator;
- baseline detector;
- use case Application.

## Passi ancora da compiere

### Step 2: Tipi di dominio principali

Implementare:

- `RegimeType`;
- `EconomicDimension`;
- `FeaturePolarity`;
- `ModelRole`;
- `RegimeProbability`;
- `FeatureDefinition`;
- `FeatureScore`;
- `FeatureSetVersion`;
- `ModelVersion`;
- `RegimeExplanation`;
- `RegimeSnapshot`.

Test attesi:

- `RegimeProbability` valida probability e rank;
- feature definition rifiuta codice/nome vuoti;
- feature score rifiuta input incoerenti;
- snapshot richiede as-of date, model version e feature set version;
- probabilita' ordinate e normalizzate.

### Step 3: Servizi di dominio base

Implementare:

- `RegimeProbabilityNormalizer`;
- `CompositeScoreCalculator`;
- `RegimeExplanationBuilder`;
- prime funzioni di supporto per driver e segnali contrari.

Test attesi:

- normalizzazione distribuzione grezza;
- gestione somma zero;
- media pesata corretta;
- driver ordinati per impatto.

### Step 4: Baseline rule-based detector v0.1

Implementare:

- `FeatureNormalizer`;
- `BaselineRegimeDetector`;
- parametri baseline v0.1;
- mapping iniziale verso regimi:
  - `Goldilocks`;
  - `Reflation`;
  - `LateCycleOverheating`;
  - `Stagflation`;
  - `DeflationBust`;
  - `UncertainTransition`.

Test attesi:

- scenario neutrale;
- scenario Goldilocks;
- scenario Reflation;
- scenario Stagflation;
- scenario DeflationBust;
- segnali divergenti;
- dimensioni mancanti.

### Step 5: Application layer minimale

Implementare:

- command `CalculateRegimeCommand`;
- use case `CalculateRegimeUseCase`;
- porte per snapshot provider, model version provider e feature set provider;
- DTO applicativo o response model;
- fake/in-memory providers per test.

Regole:

- Application non deve dipendere da Infrastructure;
- nessun EF Core;
- nessun HTTP;
- nessuna persistenza diretta.

### Step 6: Persistenza e reporting solo dopo core stabile

Solo dopo test verdi su Domain e Application:

- introdurre `MacroRegime.Infrastructure`;
- mappare snapshot e run persistenti;
- recuperare import/as-of dal prototipo Finance;
- introdurre `MacroRegime.Reporting`;
- generare report markdown;
- valutare UI Web.

## Rischi da monitorare

| Rischio | Contromisura |
|---|---|
| Reintrodurre EF nel domain core | Controllo architetturale a ogni milestone |
| Far crescere troppo il detector baseline | Servizi piccoli e testati separatamente |
| Copiare troppo dal prototipo Finance | Usare `prototype_mapping.md` come filtro |
| Rimandare spiegabilita' | `RegimeExplanation` nel domain core, non nella UI |
| Confondere primary e operational regime | Modellarli separatamente in `RegimeSnapshot` |
| Trattare `UncertainTransition` come errore | Test dedicati e scenario divergente obbligatorio |

## Decisione per il prossimo checkpoint

Il prossimo checkpoint deve completare i tipi di dominio principali e preparare il terreno al baseline detector.

Definition of Done proposta per Step 2:

- enum e record principali implementati;
- test puri verdi;
- build verde;
- nessuna dipendenza vietata;
- `RegimeSnapshot` modellato ma non ancora collegato a persistenza;
- `RegimeProbability` validata e ordinabile.

## Nota git

Il comando `git status` e' stato ostacolato dalla protezione `dubious ownership` sul repository padre `C:\ProgettiAzure\Codex`. Non e' stata modificata la configurazione globale git. Le verifiche sono state effettuate tramite build, test e listing mirato dei file.
