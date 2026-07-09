# Macro-Regime audit dopo Step 4

Data: 2026-07-02

## Scopo

Questo documento verifica lo stato del progetto prima di passare allo Step 5.

Le domande a cui risponde sono:

- quanto fatto e' coerente con il piano?
- gli Step 2, 3 e 4 sono completi rispetto alla Definition of Done prevista?
- abbiamo lasciato indietro qualcosa di necessario prima dell'Application layer?
- abbiamo anticipato codice che doveva restare fuori dal domain core?
- quali rischi o lacune vanno portati nello Step 5?

## Fonti verificate

Sono stati verificati:

- `macro_regime_plan.step1_done.md`
- `docs/domain/domain_core_design.md`
- `docs/testing/macro_regime_test_plan.md`
- `docs/adr/0001-restart-architetturale.md`
- `docs/adr/0002-dipendenze-layer.md`
- sorgenti in `src/MacroRegime.Domain`
- sorgenti in `src/MacroRegime.Application`
- test in `tests/MacroRegime.Domain.Tests`
- solution `MacroRegime.slnx`

## Verdetto sintetico

Il lavoro fatto fino allo Step 4 e' coerente con il piano e puo' essere considerato pronto per lo Step 5, con alcune lacune note da non dimenticare.

Il progetto ha correttamente mantenuto il cuore del calcolo nel dominio puro. Non risultano introdotti:

- Infrastructure;
- Reporting;
- Web;
- EF Core;
- ASP.NET;
- HTTP;
- accesso file system;
- clock di sistema;
- persistenza;
- import dati live;
- allocation engine.

Non e' stato implementato lo Step 5. Questo e' corretto: non esistono ancora `CalculateRegimeCommand`, `CalculateRegimeUseCase`, porte applicative o provider fake.

## Allineamento Step 2

Lo Step 2 richiedeva i tipi di dominio principali:

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

Stato: completato.

I test attesi sono presenti:

- `RegimeProbability` valida probability e rank;
- `FeatureDefinition` rifiuta codice/nome vuoti;
- `FeatureScore` rifiuta input incoerenti;
- `RegimeSnapshot` richiede as-of date, model version e feature set version;
- probabilita' ordinate e normalizzate.

Nota: `MacroObservation`, `MarketObservation` e `DataSnapshot` erano nel domain core design, ma non erano stati inclusi nella lista operativa dello Step 2. Sono stati introdotti nello Step 4 per rendere invocabile `FeatureNormalizer`, scelta coerente con il piano.

## Allineamento Step 3

Lo Step 3 richiedeva:

- `RegimeProbabilityNormalizer`;
- `CompositeScoreCalculator`;
- `RegimeExplanationBuilder`;
- prime funzioni di supporto per driver e segnali contrari.

Stato: completato.

I test attesi sono presenti:

- normalizzazione distribuzione grezza;
- gestione somma zero;
- media pesata corretta;
- driver ordinati per impatto.

Regola scelta e documentata nel codice/test:

- se la distribuzione grezza ha somma zero, il normalizer restituisce una distribuzione uniforme sui regimi ricevuti.

## Allineamento Step 4

Lo Step 4 richiedeva:

- `FeatureNormalizer`;
- `BaselineRegimeDetector`;
- parametri baseline v0.1;
- mapping iniziale verso:
  - `Goldilocks`;
  - `Reflation`;
  - `LateCycleOverheating`;
  - `Stagflation`;
  - `DeflationBust`;
  - `UncertainTransition`.

Stato: completato per baseline v0.1.

Sono stati aggiunti:

- `DataSnapshot`;
- `MacroObservation`;
- `MarketObservation`;
- `FeatureNormalizationResult`;
- `FeatureNormalizer`;
- `BaselineRegimeParameters`;
- `BaselineRegimeDetector`.

I test attesi sono presenti:

- scenario neutrale;
- scenario Goldilocks;
- scenario Reflation;
- scenario Stagflation;
- scenario DeflationBust;
- segnali divergenti;
- dimensioni mancanti.

Il detector produce un `RegimeSnapshot` con:

- as-of date;
- model version;
- feature set version;
- primary regime;
- operational regime;
- confidence;
- composite score;
- probabilita' normalizzate;
- feature scores;
- explanations;
- warnings.

## Cose non anticipate

Non risultano implementate funzionalita' che dovevano restare dopo Step 4:

- nessun Application use case;
- nessun command/query applicativo;
- nessuna porta `IDataSnapshotProvider`;
- nessun provider model version;
- nessun provider feature set;
- nessun progetto `MacroRegime.Infrastructure`;
- nessun progetto `MacroRegime.Reporting`;
- nessun progetto `MacroRegime.Web`;
- nessuna persistenza;
- nessun import FRED/ALFRED;
- nessun report markdown/HTML generato dal sistema;
- nessuna proposta di asset allocation.

Questo conferma che lo Step 5 non e' stato anticipato.

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
Superato: 69/69
```

Nota: un primo lancio parallelo di build e test ha causato un lock temporaneo sul file `MacroRegime.Domain.dll` in `obj`. Il test e' stato rilanciato da solo ed e' passato. Non e' un difetto funzionale del codice.

Controllo architetturale:

```text
rg "EntityFramework|AspNetCore|DbContext|DbSet|HttpClient|Sqlite|SqlConnection|File\.|Directory\.|DateTime\.Now|DateTimeOffset\.Now" src/MacroRegime.Domain src/MacroRegime.Application
```

Risultato:

- nessun match nei sorgenti Domain/Application.

Controllo Step 5 non anticipato:

```text
rg "CalculateRegimeCommand|CalculateRegimeUseCase|IDataSnapshotProvider|IModelVersionProvider|IFeatureSetProvider|MacroRegime.Infrastructure|MacroRegime.Reporting|MacroRegime.Web" src tests
```

Risultato:

- nessun match nei sorgenti/test.

## Lacune e rischi da portare avanti

### 1. Semantica driver/contrary ancora semplificata

`RegimeExplanationBuilder` usa una logica iniziale risk-on/risk-off. Questo e' sufficiente per i test Step 3/4, ma non e' ancora una semantica macro completa.

Esempio: una feature come `INFL_PRESS` puo' essere un driver positivo per `Stagflation`, ma non e' naturalmente risk-on. Prima di rendere il modello piu' sofisticato, conviene introdurre una mappa regime-specifica dei driver attesi.

Impatto:

- non blocca Step 5;
- va corretto prima di considerare le explanations affidabili per uso informativo serio.

### 2. `FeaturePolarity` non e' applicata alle formule hardcoded

Le formule esplicite di `FeatureNormalizer` decidono direttamente il significato dello score. Questo e' accettabile per baseline v0.1, ma rende `FeaturePolarity` non sempre determinante.

Impatto:

- non blocca Step 5;
- va chiarito quando si separeranno formula, polarita' e interpretazione.

### 3. Test as-of su `DataSnapshot` ancora parziali

`DataSnapshot.TryGetValue` filtra osservazioni macro per `PublicationDate` e market per `AvailabilityDate`, ma manca un test dedicato che dimostri che una pubblicazione futura non viene usata.

Impatto:

- e' una lacuna di test rilevante;
- consigliato aggiungerla prima o durante Step 5, perche' l'Application layer usera' snapshot as-of.

### 4. Test di validazione osservazioni non completi

`MacroObservation` e `MarketObservation` validano codice/simbolo e nome, ma non hanno test dedicati.

Impatto:

- non blocca Step 5;
- da completare nel prossimo giro di hardening del dominio.

### 5. Baseline v0.1 e' intenzionalmente euristica

Le soglie sono deterministicamente codificate e solo `confirmation_threshold` entra da `ModelVersion.Parameters`.

Impatto:

- coerente con il piano;
- prima di uso reale bisogna espandere la model card e rendere soglie/formule piu' esplicite.

### 6. Documento checkpoint non ancora aggiornato dopo Step 2-4

`macro_regime_plan.step1_done.md` resta il checkpoint di chiusura Step 1. Questo audit colma la verifica fino allo Step 4, ma non sostituisce un eventuale documento narrativo di avanzamento complessivo.

Impatto:

- non blocca Step 5;
- utile creare un checkpoint `step4_done` se vogliamo mantenere la stessa disciplina documentale.

## Decisione proposta

Si puo' procedere allo Step 5.

Definition of Ready per Step 5:

- Domain compila;
- Domain tests verdi;
- baseline detector istanziabile in test puri;
- niente dipendenze vietate;
- nessuna persistenza anticipata;
- nessun use case gia' presente;
- lacune note registrate in questo documento.

## Backlog minimo prima/durante Step 5

Priorita' alta:

- aggiungere test `DataSnapshot` su publication/availability future;
- definire porte Application senza accedere a Infrastructure;
- introdurre `CalculateRegimeCommand`;
- introdurre `CalculateRegimeUseCase`;
- testare use case con provider fake/in-memory.

Priorita' media:

- aggiungere test validazione `MacroObservation` e `MarketObservation`;
- rendere piu' esplicita la semantica driver/contrary;
- valutare una mappa regime-specifica dei segnali attesi.

Fuori scope Step 5:

- EF Core;
- import dati live;
- reporting;
- UI;
- allocation engine.
