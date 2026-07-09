# Piano di restart architetturale Macro-Regime

Data: 2026-07-02

## Scopo

Questo documento definisce il piano di restart architetturale del Macro-Regime Engine prima della creazione dello scheletro C# serio.

Il restart non e' una riscrittura cieca. E' una ripartenza controllata che recupera dal prototipo Finance cio' che e' valido, ma ricostruisce il cuore del sistema secondo la governance definita in:

- `macro_regime_governance.md`
- `macro_regime_delivery_plan.md`
- `macro_regime_postmortem.md`

## Decisione

La decisione e':

> avviare un restart architetturale del Macro-Regime Engine, costruendo prima un core C# puro e testabile, poi reintroducendo persistenza, reportistica e UI come adapter.

Il codice in `C:\ProgettiAzure\Codex\Finance` resta una reference implementation, non la base diretta da modificare.

## Obiettivi del restart

1. Separare dominio, use case, infrastruttura e UI.
2. Rendere il baseline detector testabile senza database.
3. Rendere espliciti versioni, formule, soglie e model card.
4. Conservare il concetto as-of/vintage-aware.
5. Separare regime detection, allocation proposal e decisione umana.
6. Recuperare fixture e scenari dal prototipo Finance.
7. Preparare un percorso incrementale verso un sistema applicativo completo.

## Non-obiettivi iniziali

Per la prima fase del restart sono fuori scope:

- API FRED/ALFRED reali;
- download dati live;
- HMM in produzione;
- clustering in produzione;
- UI MVC completa;
- EF Core persistence;
- ottimizzazione portafoglio avanzata;
- fiscalita' reale dettagliata;
- esecuzione ordini.

## Architettura target

```text
MacroRegime.sln
src/
  MacroRegime.Domain/
  MacroRegime.Application/
  MacroRegime.Infrastructure/
  MacroRegime.Reporting/
  MacroRegime.Web/
tests/
  MacroRegime.Domain.Tests/
  MacroRegime.Application.Tests/
  MacroRegime.Infrastructure.Tests/
research/
  regime-eval/
docs/
  adr/
```

## Regole di dipendenza

```text
MacroRegime.Domain
  nessuna dipendenza applicativa, EF, web, file system, database, HTTP

MacroRegime.Application
  dipende da Domain
  definisce use case, porte, comandi, query e DTO applicativi

MacroRegime.Infrastructure
  dipende da Application e Domain
  implementa repository, import dati, EF Core, provider esterni

MacroRegime.Reporting
  dipende da Application e Domain
  produce report markdown/HTML/JSON

MacroRegime.Web
  dipende da Application, Reporting e Infrastructure
  visualizza output gia' prodotti dai use case
```

Regola non negoziabile:

> `MacroRegime.Domain` non deve contenere riferimenti a Entity Framework, ASP.NET, HTTP, SQLite, file system o clock di sistema.

## Artefatti da creare prima dello scheletro

Prima di creare la solution occorre avere:

1. `macro_regime_postmortem.md`
2. `macro_regime_architectural_restart_plan.md`
3. `docs/adr/0001-restart-architetturale.md`
4. `docs/adr/0002-dipendenze-layer.md`
5. `docs/domain/macro_regime_glossary.md`
6. `docs/domain/prototype_mapping.md`

Solo i primi due sono creati in questa fase. Gli ADR e i documenti domain saranno il prossimo passo operativo.

## Fase R0: Baseline documentale

### Obiettivo

Chiudere la fase di diagnosi e fissare la decisione di restart.

### Deliverable

- `macro_regime_postmortem.md`
- `macro_regime_architectural_restart_plan.md`

### Definition of Done

- Il prototipo Finance e' classificato come reference implementation.
- Sono elencati elementi da recuperare e da scartare.
- La decisione restart vs refactor e' esplicita.
- Il piano indica cosa fare prima dello scheletro C#.

## Fase R1: ADR minime

### Obiettivo

Scrivere le decisioni architetturali essenziali prima del codice.

### Deliverable

#### `docs/adr/0001-restart-architetturale.md`

Deve contenere:

- contesto;
- problema del prototipo;
- decisione restart;
- alternative considerate;
- conseguenze positive;
- conseguenze negative;
- vincoli.

#### `docs/adr/0002-dipendenze-layer.md`

Deve contenere:

- regole fra Domain, Application, Infrastructure, Reporting, Web;
- dipendenze vietate;
- dipendenze consentite;
- esempi concreti;
- test di accettazione.

### Definition of Done

- Gli ADR sono leggibili senza conoscere tutta la conversazione.
- Ogni ADR ha stato `Accepted`.
- Ogni ADR indica almeno una conseguenza negativa.

## Fase R2: Glossario e mapping prototipo

### Obiettivo

Evitare di perdere il lavoro utile del primo tentativo e tradurlo in un nuovo modello pulito.

### Deliverable

#### `docs/domain/macro_regime_glossary.md`

Deve definire:

- Regime;
- Macro regime;
- Market regime;
- Portfolio regime;
- As-of date;
- Observation date;
- Publication date;
- Availability date;
- Vintage;
- Feature;
- Feature set version;
- Model version;
- Regime run;
- Regime probability;
- Regime explanation;
- Allocation proposal;
- Decision record.

#### `docs/domain/prototype_mapping.md`

Deve mappare:

| Prototipo Finance | Nuovo sistema | Azione |
|---|---|---|
| `MacroDataSource` | `MacroDataSource` o source metadata | recuperare |
| `MacroSeries` | `MacroSeriesDefinition` | rivedere |
| `MacroObservation` | `MacroObservation` value/data record | recuperare concetto |
| `DataVintage` | `DataVintage` / `DataSnapshot` | recuperare |
| `RegimeCalculationService` | baseline use case + domain detector | spezzare |
| `RegimeRun` | `RegimeRunSnapshot` / persisted run | separare dominio/persistenza |
| `MacroRegimeController` | futura UI | rimandare |
| seed demo | fixtures | recuperare |

### Definition of Done

- Ogni concetto Finance importante ha una destinazione.
- Ogni elemento e' marcato come recuperare, rivedere, spezzare, scartare o rimandare.
- Il mapping guida la creazione del nuovo dominio.

## Fase R3: Design del domain core

### Obiettivo

Definire il dominio prima di generare progetti C#.

### Deliverable

`docs/domain/domain_core_design.md`

Deve contenere:

- value object;
- enum/tipi;
- aggregate o record principali;
- servizi di dominio;
- invarianti;
- errori;
- esempi di input/output.

### Value object iniziali

- `AsOfDate`
- `ObservationDate`
- `PublicationDate`
- `AvailabilityDate`
- `Probability`
- `RegimeConfidence`
- `FeatureWeight`
- `NormalizedScore`

### Tipi principali

- `RegimeType`
- `EconomicDimension`
- `FeatureDefinition`
- `FeatureObservation`
- `FeatureScore`
- `RegimeProbability`
- `RegimeSnapshot`
- `RegimeExplanation`
- `BaselineModelVersion`

### Servizi di dominio iniziali

- `FeatureNormalizer`
- `CompositeScoreCalculator`
- `BaselineRegimeDetector`
- `RegimeProbabilityNormalizer`
- `RegimeExplanationBuilder`

### Invarianti minime

- probabilita' fra 0 e 1;
- confidence fra 0 e 1;
- weight non negativo;
- score normalizzato fra 0 e 1;
- snapshot con as-of date obbligatoria;
- regime probabilities ordinate e con somma controllata;
- `UncertainTransition` quando confidence sotto soglia o segnali divergenti.

## Fase R4: Test plan prima del codice

### Obiettivo

Definire test attesi prima dello scheletro.

### Deliverable

`docs/testing/macro_regime_test_plan.md`

### Test minimi Domain

- `Probability` rifiuta valori minori di 0 e maggiori di 1.
- `RegimeProbabilityNormalizer` normalizza una distribuzione grezza.
- `BaselineRegimeDetector` produce `UncertainTransition` con segnali divergenti.
- `BaselineRegimeDetector` non produce allarmi estremi con dati neutrali.
- `RegimeExplanationBuilder` restituisce driver ordinati per impatto.
- `CompositeScoreCalculator` rispetta pesi e score.

### Test minimi Application

- use case calcola snapshot da input in memoria;
- use case non persiste direttamente;
- use case restituisce warnings per dimensioni mancanti;
- use case include model version e feature set version.

## Fase R5: Creazione scheletro C#

Questa fase inizia solo dopo R1-R4.

### Comandi indicativi

```text
dotnet new sln -n MacroRegime
dotnet new classlib -n MacroRegime.Domain -o src/MacroRegime.Domain
dotnet new classlib -n MacroRegime.Application -o src/MacroRegime.Application
dotnet new xunit -n MacroRegime.Domain.Tests -o tests/MacroRegime.Domain.Tests
dotnet sln MacroRegime.sln add src/MacroRegime.Domain/MacroRegime.Domain.csproj
dotnet sln MacroRegime.sln add src/MacroRegime.Application/MacroRegime.Application.csproj
dotnet sln MacroRegime.sln add tests/MacroRegime.Domain.Tests/MacroRegime.Domain.Tests.csproj
```

La scelta fra `.sln` e `.slnx` sara' documentata in ADR o decisa in base al runtime locale.

### Definition of Done

- solution creata;
- Domain compila;
- Application compila;
- test project compila;
- test iniziali verdi;
- nessun riferimento a EF Core;
- nessun riferimento a ASP.NET;
- nessun riferimento a Infrastructure.

## Sequenza operativa per Codex

Quando verra' richiesto di procedere, Codex dovra':

1. Creare `docs/adr/`.
2. Creare `docs/domain/`.
3. Creare `docs/testing/`.
4. Scrivere ADR 0001.
5. Scrivere ADR 0002.
6. Scrivere glossario dominio.
7. Scrivere mapping prototipo.
8. Scrivere design domain core.
9. Scrivere test plan.
10. Solo dopo creare lo scheletro C#.

## Gate prima dello scheletro

Lo scheletro C# puo' essere creato solo se:

- post-mortem approvato;
- restart plan approvato;
- ADR 0001 presente;
- ADR 0002 presente;
- glossario presente;
- mapping prototipo presente;
- domain core design presente;
- test plan presente.

## Criteri di qualita' del nuovo sistema

Il nuovo sistema dovra':

- rendere il calcolo del regime una funzione di dominio testabile;
- usare persistenza solo come adapter;
- distinguere input disponibili as-of da dati revisionati;
- salvare probabilita', non solo etichette;
- spiegare driver e segnali contrari;
- mantenere `UncertainTransition` come stato operativo reale;
- separare detection, allocation proposal e decision record;
- permettere challenger model senza cambiare il core baseline.

## Riuso controllato dal prototipo Finance

### Riusare subito

- naming principale;
- lista regimi;
- dimensioni macro;
- seed scenario;
- test vintage/as-of;
- test idempotenza run.

### Riusare dopo il core

- DbContext;
- schema EF;
- import FRED/FRED-MD;
- dashboard MVC;
- report demo.

### Non riusare come base

- `RegimeCalculationService` monolitico;
- formule dentro Infrastructure;
- creazione implicita di versioni nel calcolo;
- persistenza dentro il detector.

## Prossima azione

La prossima azione e' creare gli ADR e i documenti di dominio previsti dalle fasi R1-R4. Dopo quel checkpoint sara' possibile generare lo scheletro C# con una direzione piu' pulita.
