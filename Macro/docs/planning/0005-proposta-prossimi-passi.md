# Proposta prossimi passi

Data: 2026-07-02

## Piano operativo proposto

Prima chiudere la fase di orientamento, poi partire con una prima vertical slice C# piccola e testabile.

## 1. Verificare il primo tentativo C#

- Cercare se il codice esiste nel workspace o in un'altra cartella.
- Se esiste: analizzarlo.
- Se non esiste nel workspace corrente: documentare che non e' disponibile e autorizzare un restart pulito.

## 2. Scrivere `macro_regime_postmortem.md`

Il documento deve chiarire:

- cosa non ha funzionato;
- cosa recuperare;
- cosa scartare;
- decisione finale: refactor o restart.

## 3. Creare una prima ADR

File consigliato:

- `docs/adr/0001-architettura-modulare-csharp.md`

Decisione:

- architettura C# separata in Domain, Application, Infrastructure, Reporting e Web.

Motivazione:

- evitare che UI, database o modelli avanzati contaminino il dominio.

## 4. Preparare lo scheletro della solution

Struttura iniziale:

```text
MacroRegime.sln
src/
  MacroRegime.Domain/
  MacroRegime.Application/
tests/
  MacroRegime.Domain.Tests/
```

## 5. Milestone 1: Domain Core

Primo obiettivo tecnico reale:

- value object per date e probabilita';
- enum o tipi per regime e dimensioni macro;
- `RegimeProbability`;
- `RegimeSnapshot`;
- `RegimeExplanation`;
- test unitari.

## 6. Checkpoint dopo Milestone 1

Verificare:

- build verde;
- test verdi;
- dominio isolato;
- nessuna dipendenza da database, API o UI;
- coerenza con governance.

Solo dopo questo checkpoint si passa alla baseline rule-based.

## Proposta operativa

Nel passaggio successivo Codex dovra':

1. ispezionare il workspace alla ricerca del primo tentativo C#;
2. analizzare il codice disponibile;
3. preparare `macro_regime_postmortem.md`;
4. decidere se procedere con refactor o restart pulito dalla Milestone 1.
