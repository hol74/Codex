# Delivery plan del progetto Macro-Regime

## Scopo

Questo documento traduce la governance del progetto Macro-Regime in un piano di esecuzione. Il progetto sara' sviluppato in C# come runtime applicativo principale, con eventuale research lab Python separato per modelli avanzati.

Codex sara' l'esecutore operativo: implementera' milestone, aggiornera' documentazione, eseguira' test e segnalera' blocchi o deviazioni. L'owner umano approvera' scelte di policy, promozione di modelli e decisioni allocative.

## Stato di partenza

Documenti disponibili:

- `macro_regime.md`;
- `macro_regime_github.md`;
- `macro_regime_plan.md`;
- `chat1.md`;
- `macro_regime_governance.md`.

Problema identificato:

- il primo tentativo C# non e' stato soddisfacente;
- il piano precedente entra troppo rapidamente in implementazione applicativa;
- serve una sequenza piu' disciplinata: dominio, baseline, audit trail, proposta allocativa, UI, ricerca avanzata.

## Strategia di delivery

La strategia e' costruire una vertical slice minima ma corretta, poi estenderla.

Ordine:

1. Analizzare o archiviare il primo tentativo.
2. Definire domain core puro.
3. Implementare baseline rule-based.
4. Aggiungere audit trail e as-of semantics.
5. Aggiungere allocation proposal vincolata.
6. Aggiungere reporting/UI.
7. Aprire research lab per modelli avanzati.

## Architettura target

```text
src/
  MacroRegime.Domain/
  MacroRegime.Application/
  MacroRegime.Infrastructure/
  MacroRegime.Reporting/
  MacroRegime.Web/
tests/
  MacroRegime.Domain.Tests/
  MacroRegime.Application.Tests/
research/
  regime-eval/
docs/
```

## Regole architetturali

- `MacroRegime.Domain` non dipende da EF Core, web framework, file system o API esterne.
- `MacroRegime.Application` orchestra casi d'uso e porte.
- `MacroRegime.Infrastructure` implementa persistenza, import dati e adapter esterni.
- `MacroRegime.Reporting` produce report leggibili e snapshot.
- `MacroRegime.Web` visualizza dati gia' prodotti dall'application layer.
- I test del dominio devono poter girare senza database.
- Il seed demo deve essere deterministico.

## Milestone 0: Post-mortem del primo tentativo

### Obiettivo

Capire cosa non ha funzionato nel primo tentativo e decidere se recuperare codice o ripartire.

### Attivita'

- Individuare eventuale codice esistente.
- Valutare struttura, dipendenze, dominio, test e UI.
- Separare difetti accidentali da difetti concettuali.
- Salvare una nota di post-mortem.

### Deliverable

- `macro_regime_postmortem.md`.

### Definition of Done

- Il primo tentativo e' stato descritto.
- Sono indicate parti recuperabili.
- Sono indicate parti da scartare.
- Esiste una decisione: refactor o restart.

### Criteri di accettazione

- Nessuna nuova implementazione parte prima del post-mortem, se il vecchio codice e' disponibile.
- Se il vecchio codice non e' presente nel workspace, il post-mortem lo dichiara e autorizza restart.

## Milestone 1: Domain Core

### Obiettivo

Costruire il nucleo di dominio C# testabile in memoria.

### Entita' e value object iniziali

- `AsOfDate`;
- `ObservationDate`;
- `PublicationDate`;
- `AvailabilityDate`;
- `MacroDataSource`;
- `MacroSeries`;
- `MacroObservation`;
- `EconomicDimension`;
- `FeatureDefinition`;
- `FeatureValue`;
- `RegimeType`;
- `RegimeProbability`;
- `RegimeSnapshot`;
- `RegimeExplanation`.

### Servizi di dominio iniziali

- validazione date;
- normalizzazione feature demo;
- costruzione snapshot regime;
- ordinamento probabilita';
- identificazione driver e segnali contrari.

### Deliverable

- progetto `MacroRegime.Domain`;
- progetto `MacroRegime.Domain.Tests`;
- test unitari per value object e snapshot.

### Definition of Done

- Build verde.
- Test del dominio verdi.
- Nessuna dipendenza da infrastruttura.
- Uno snapshot demo puo' essere costruito in memoria.

### Criteri di accettazione

- Il dominio compila senza EF Core.
- Le date as-of non sono semplici stringhe sparse.
- Le probabilita' dei regimi sono validate.
- La somma delle probabilita' e' controllata o normalizzata esplicitamente.

## Milestone 2: Baseline Rule-Based Regime Detector

### Obiettivo

Implementare il primo motore interpretabile, da usare come baseline permanente.

### Componenti

- `GrowthScore`;
- `InflationScore`;
- `RiskScore`;
- `MonetaryScore`;
- eventuale `LiquidityScore`;
- composite score configurabile;
- mapping fuzzy verso regimi;
- stato `UncertainTransition`;
- driver e segnali contrari.

### Regimi minimi

- `ExpansionRiskOn`;
- `InflationaryExpansion`;
- `Slowdown`;
- `RecessionStress`;
- `Recovery`;
- `UncertainTransition`.

### Deliverable

- progetto `MacroRegime.Application`;
- servizio `BaselineRegimeDetector`;
- seed demo in memoria;
- test su casi sintetici.

### Definition of Done

- Almeno 5 scenari sintetici testati.
- Il detector restituisce probabilita', non solo etichetta.
- `UncertainTransition` appare quando segnali principali divergono.
- Ogni output include driver e segnali contrari.

### Criteri di accettazione

- Un cambio di singola feature non deve ribaltare sempre il regime.
- Le soglie sono leggibili e versionabili.
- Il modello e' documentabile con model card minima.

## Milestone 3: Audit Trail e As-Of Semantics

### Obiettivo

Rendere ogni calcolo riproducibile e resistente al look-ahead bias.

### Componenti

- `DataSnapshot`;
- `FeatureSetVersion`;
- `RegimeModelVersion`;
- `RegimeRun`;
- `RegimeRunInput`;
- `RegimeRunOutput`;
- `RegimeRunExplanation`.

### Deliverable

- modello applicativo per run auditabile;
- repository interface in application layer;
- implementazione iniziale in memoria;
- report tecnico di un run demo.

### Definition of Done

- Ogni run ha as-of date, execution timestamp, versioni e input.
- Ogni feature conserva legame con dati disponibili alla data.
- Il report demo mostra cosa il sistema sapeva in quel momento.

### Criteri di accettazione

- Non si puo' creare un run senza model version.
- Non si puo' creare un run senza feature set version.
- La spiegazione e' salvata insieme all'output.

## Milestone 4: Allocation Proposal Vincolata

### Obiettivo

Tradurre regime e probabilita' in proposta allocativa prudente, non in decisione automatica.

### Componenti

- `StrategicAllocationPolicy`;
- `AssetClass`;
- `AllocationBand`;
- `CurrentPortfolio`;
- `TargetAllocation`;
- `RegimeTiltRule`;
- `TurnoverConstraint`;
- `CostConstraint`;
- `LiquidityConstraint`;
- `TaxConstraintPlaceholder`;
- `AllocationProposal`;
- `DecisionSuggestion`.

### Decisioni suggerite

- `Hold`;
- `WaitForConfirmation`;
- `PartialRebalance`;
- `FullRebalance`;
- `ManualReviewRequired`.

### Deliverable

- policy demo;
- servizio `AllocationProposalService`;
- test su regimi diversi;
- report proposta demo.

### Definition of Done

- La proposta non supera le bande.
- Il turnover massimo e' rispettato.
- I costi possono bloccare una proposta.
- Lo stato incerto riduce turnover e preferisce attesa.
- Il cash e' modellato come asset class.

### Criteri di accettazione

- Nessuna allocazione negativa in portafogli long-only.
- Nessun all-in/all-out.
- Ogni tilt ha motivazione.
- Ogni blocco di vincolo e' visibile.

## Milestone 5: Reporting e UI minima

### Obiettivo

Rendere il sistema leggibile con report e dashboard sobria.

### Componenti

- report mensile markdown o HTML;
- vista regime probabilistico;
- vista feature correnti;
- vista driver e segnali contrari;
- vista proposta allocativa;
- vista audit trail.

### Deliverable

- `MacroRegime.Reporting`;
- eventuale `MacroRegime.Web`;
- report demo generato da seed.

### Definition of Done

- Il report e' generabile da CLI/test o servizio applicativo.
- La UI non contiene testo marketing.
- La UI mostra dati, stato, driver, vincoli e azioni.
- Il report collega regime, rischio e proposta allocativa.

### Criteri di accettazione

- Il report mensile contiene probabilita' per regime.
- Il report mostra variazione rispetto al periodo precedente se disponibile.
- Il report mostra costo/turnover stimato quando c'e' una proposta.

## Milestone 6: Research Lab

### Obiettivo

Valutare modelli avanzati senza contaminare il runtime applicativo.

### Componenti

- cartella `research/regime-eval/`;
- notebook o script Python;
- HMM;
- clustering;
- Markov switching;
- walk-forward;
- stress test;
- confronto contro baseline.

### Deliverable

- protocollo di valutazione;
- dataset demo o sample;
- report confronto baseline/challenger;
- model card per ogni challenger.

### Definition of Done

- Nessun modello avanzato e' usato dal runtime senza promozione.
- Ogni challenger ha metriche out-of-sample.
- Ogni challenger e' confrontato con baseline rule-based.
- I risultati negativi vengono conservati.

### Criteri di accettazione

- Il research lab puo' usare Python.
- Il runtime applicativo resta C#.
- La promozione richiede Model Gate.

## Backlog iniziale per Codex

### Blocco A: Documentazione e orientamento

1. Verificare presenza di codice C# esistente.
2. Scrivere `macro_regime_postmortem.md`.
3. Se serve, creare `docs/adr/`.
4. Creare ADR iniziale su architettura modulare C#.

### Blocco B: Soluzione C#

1. Creare solution `.sln`.
2. Creare `MacroRegime.Domain`.
3. Creare `MacroRegime.Domain.Tests`.
4. Configurare test runner.
5. Aggiungere value object di date e probabilita'.

### Blocco C: Baseline demo

1. Definire regimi.
2. Definire dimensioni macro.
3. Implementare feature score.
4. Implementare detector baseline.
5. Testare scenari sintetici.

### Blocco D: Audit

1. Definire model version.
2. Definire feature set version.
3. Definire regime run.
4. Implementare run in memoria.
5. Generare report tecnico.

### Blocco E: Allocation

1. Definire asset class.
2. Definire policy strategica.
3. Definire bande.
4. Implementare tilt rules.
5. Implementare vincoli.
6. Generare proposta demo.

## Sequenza di esecuzione per Codex

Quando iniziera' l'implementazione, Codex dovra':

1. Ispezionare il workspace.
2. Identificare eventuale codice esistente.
3. Scrivere o aggiornare il post-mortem.
4. Proporre la struttura della solution.
5. Implementare solo Milestone 1.
6. Eseguire build e test.
7. Fermarsi a riepilogare risultato e rischi prima di passare a Milestone 2, salvo richiesta esplicita di continuare.

## Metriche di successo

### Tecniche

- build verde;
- test automatici verdi;
- dominio isolato;
- nessuna dipendenza esterna nella baseline;
- run demo riproducibile.

### Di dominio

- probabilita' di regime disponibili;
- driver e segnali contrari leggibili;
- stato incerto gestito;
- cash esplicito;
- vincoli allocativi rispettati.

### Di governance

- versioni dati/feature/modello registrate;
- decisioni spiegabili;
- documentazione aggiornata;
- deviazioni motivate.

## Rischi e contromisure

| Rischio | Contromisura |
|---|---|
| Ripartire troppo presto dalla UI | Milestone 1-4 prima della UI |
| Codice accoppiato al database | Domain puro e repository interface |
| Modello troppo complesso | Baseline rule-based prima |
| Backtest contaminato | As-of semantics e publication date |
| Ricerca infinita | Challenger isolati e Model Gate |
| Allocazioni estreme | Bande, turnover e costi |
| Mancanza di spiegabilita' | Driver e segnali contrari obbligatori |

## Definition of Done complessiva della prima release

La prima release informativa e' completa quando:

- esiste una solution C# compilabile;
- il dominio e' testato;
- un seed demo genera feature, regime run e probabilita';
- esiste una baseline rule-based;
- esiste audit trail minimo;
- esiste una proposta allocativa vincolata demo;
- esiste un report leggibile;
- tutti i test automatici sono verdi;
- la documentazione principale e' aggiornata.

## Fuori scope per la prima release

- API reali FRED/ALFRED;
- HMM in produzione;
- clustering in produzione;
- ottimizzazione Markowitz completa;
- fiscalita' reale dettagliata;
- esecuzione ordini;
- trading automatico;
- raccomandazioni non vincolate da policy.

## Prossima azione

La prossima azione operativa e' cercare nel workspace o in una cartella indicata dall'owner il primo tentativo C#. Se non esiste nel workspace corrente, Codex dovra' scrivere `macro_regime_postmortem.md` dichiarando che il codice non e' disponibile e autorizzando un restart pulito dalla Milestone 1.
