# Test plan Macro-Regime

Data: 2026-07-02

## Scopo

Questo documento definisce i test minimi da avere prima e durante la creazione dello scheletro C#. Il test plan serve a evitare che il nuovo sistema ripeta il problema del prototipo: calcolo funzionante ma troppo accoppiato a infrastruttura e database.

## Principi di test

1. I test del dominio non usano database.
2. I test del dominio non usano file system.
3. I test del dominio non usano HTTP.
4. I test Application usano porte fake o in-memory.
5. I test Infrastructure vengono dopo il core.
6. I casi `UncertainTransition` sono obbligatori, non edge case opzionali.

## Suite previste

```text
tests/
  MacroRegime.Domain.Tests/
  MacroRegime.Application.Tests/
  MacroRegime.Infrastructure.Tests/
```

La prima fase crea solo Domain tests e, se necessario, Application tests.

## Test Domain: value object

### `Probability`

- accetta 0;
- accetta 1;
- accetta valori intermedi;
- rifiuta valori minori di 0;
- rifiuta valori maggiori di 1.

### `RegimeConfidence`

- accetta valori fra 0 e 1;
- rifiuta valori fuori range.

### `FeatureWeight`

- accetta 0;
- accetta valori positivi;
- rifiuta valori negativi.

### `NormalizedScore`

- accetta 0;
- accetta 0.5;
- accetta 1;
- rifiuta valori fuori range.

### Date value object

Test minimi:

- `AsOfDate` non accetta `DateOnly.MinValue`;
- `PublicationDate` successiva ad as-of non e' usabile nello snapshot;
- `AvailabilityDate` successiva ad as-of non e' usabile nello snapshot.

## Test Domain: probability normalizer

### Normalizzazione base

Input:

```text
Goldilocks = 2
Reflation = 1
DeflationBust = 1
```

Atteso:

```text
Goldilocks = 0.50
Reflation = 0.25
DeflationBust = 0.25
```

### Somma zero

Input:

```text
tutti score grezzi = 0
```

Atteso:

- comportamento esplicito;
- nessuna divisione per zero;
- fallback documentato.

### Ordinamento

Le probabilita' finali devono essere ordinate per probabilita' decrescente e avere rank coerente.

## Test Domain: composite score

### Media pesata

Input:

```text
feature A score 0.60 weight 0.30
feature B score 0.40 weight 0.70
```

Atteso:

```text
0.46
```

### Peso totale zero

Atteso:

- score neutrale 0.5 oppure errore esplicito, secondo design scelto;
- comportamento documentato.

## Test Domain: baseline detector

### Scenario neutrale

Input:

- score vicini a 0.5;
- nessuna dimensione dominante.

Atteso:

- operational regime `UncertainTransition`;
- confidence bassa o moderata;
- nessuna spiegazione aggressiva.

### Scenario Goldilocks debole

Input:

- growth positivo;
- risk appetite positivo;
- inflation moderata;
- credit non stressato.

Atteso:

- primary regime `Goldilocks`;
- operational regime `Goldilocks` solo se confidence supera soglia;
- driver growth/risk.

### Scenario Reflation

Input:

- growth positivo;
- inflation in aumento;
- risk positivo.

Atteso:

- primary regime `Reflation` o probabilita' alta su Reflation;
- segnale contrario se monetary conditions sono restrittive.

### Scenario Stagflation

Input:

- growth debole;
- inflation alta;
- credit in deterioramento.

Atteso:

- alta probabilita' `Stagflation`;
- driver inflation e growth debole;
- warning se dimensione Monetary mancante.

### Scenario DeflationBust

Input:

- growth debole;
- inflation bassa;
- risk appetite debole;
- credit stress elevato.

Atteso:

- alta probabilita' `DeflationBust`;
- operational regime difensivo se confidence sopra soglia.

### Segnali divergenti

Input:

- growth forte;
- inflation alta;
- risk debole;
- credit debole.

Atteso:

- operational regime `UncertainTransition`;
- explanations includono driver e segnali contrari.

### Dimensioni mancanti

Input:

- mancano Credit e Monetary.

Atteso:

- warnings presenti;
- confidence penalizzata o operational regime `UncertainTransition`.

## Test Domain: explanations

### Driver ordinati

Le explanations di tipo `Driver` devono essere ordinate per impatto assoluto o rilevanza definita.

### Segnali contrari

Se una feature contraddice il primary regime, deve apparire come `ContrarySignal`.

### Warnings leggibili

Warnings e explanations devono essere testabili come testo stabile o tramite codici.

## Test Application

### Use case calcolo regime

Il use case deve:

- ricevere command con as-of date;
- ricevere snapshot da porta applicativa;
- ricevere feature set version;
- ricevere model version;
- chiamare domain detector;
- restituire `RegimeSnapshot` o DTO applicativo.

Non deve:

- usare EF Core;
- salvare direttamente;
- chiamare HTTP.

### Snapshot mancante

Se lo snapshot provider non restituisce dati:

- il use case produce warnings;
- il detector puo' restituire `UncertainTransition`;
- non deve fallire con eccezione non gestita.

### Versioni mancanti

Se feature set o model version mancano:

- il use case deve restituire errore applicativo chiaro;
- non deve creare versioni implicitamente nel detector.

## Test Infrastructure futuri

Da implementare dopo il core:

- mapping EF -> domain snapshot;
- mapping domain snapshot -> persisted run;
- as-of snapshot con vintage;
- import FRED/ALFRED;
- idempotenza upsert run;
- query dashboard.

## Test architetturali

Prima di considerare completata la prima milestone:

- `MacroRegime.Domain` non referenzia EF Core;
- `MacroRegime.Domain` non referenzia ASP.NET;
- `MacroRegime.Application` non referenzia Infrastructure;
- `BaselineRegimeDetector` e' istanziabile in test puri;
- nessun test Domain apre SQLite.

## Test data iniziali

Fixture da creare:

```text
NeutralScenario
GoldilocksScenario
ReflationScenario
StagflationScenario
DeflationBustScenario
DivergentSignalsScenario
MissingDimensionsScenario
VintageRevisionScenario
```

## Definition of Done test prima dello scheletro completo

Quando verra' creato lo scheletro C#:

- deve essere possibile tradurre questo piano in test xUnit;
- ogni test deve avere naming descrittivo;
- almeno i test value object e normalizer devono essere implementati nella Milestone 1;
- i test Infrastructure devono restare fuori finche' il domain core non e' stabile.
