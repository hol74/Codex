# Domain core design Macro-Regime

Data: 2026-07-02

## Scopo

Questo documento definisce il design minimo del domain core prima di generare la solution C#. Il core deve permettere di calcolare una baseline rule-based in memoria, con input espliciti e output auditabili.

## Principi

1. Il dominio non conosce database, UI o API.
2. Ogni calcolo riceve input espliciti.
3. Ogni output contiene versione modello e as-of date.
4. Le probabilita' sono sempre validate.
5. `UncertainTransition` e' un esito legittimo.
6. Le spiegazioni sono parte del risultato, non un'aggiunta UI.

## Namespace previsti

```text
MacroRegime.Domain.Common
MacroRegime.Domain.Time
MacroRegime.Domain.Data
MacroRegime.Domain.Features
MacroRegime.Domain.Models
MacroRegime.Domain.Regimes
MacroRegime.Domain.Explanations
```

La struttura fisica potra' essere piu' semplice nella prima iterazione, ma questi confini concettuali devono restare chiari.

## Value object

### `AsOfDate`

Rappresenta la data di conoscenza del sistema.

Invarianti:

- obbligatoria;
- non deve essere `DateOnly.MinValue`;
- nel dominio non legge il clock di sistema.

### `ObservationDate`

Data del fenomeno osservato.

Invarianti:

- obbligatoria;
- non deve essere successiva alla publication date quando entrambe sono presenti.

### `PublicationDate`

Data in cui la fonte pubblica il dato.

Invarianti:

- obbligatoria per dati macro;
- deve essere minore o uguale alla as-of date per essere usabile.

### `AvailabilityDate`

Data in cui il sistema puo' usare il dato.

Invarianti:

- obbligatoria per dati market e snapshot;
- deve essere minore o uguale alla as-of date per essere usabile.

### `Probability`

Numero decimale fra 0 e 1.

Invarianti:

- `0 <= value <= 1`.

### `RegimeConfidence`

Numero decimale fra 0 e 1 che misura la forza del regime operativo.

Invarianti:

- `0 <= value <= 1`.

### `FeatureWeight`

Peso non negativo di una feature.

Invarianti:

- `value >= 0`.

### `NormalizedScore`

Score normalizzato fra 0 e 1.

Invarianti:

- `0 <= value <= 1`;
- 0.5 rappresenta neutralita' nella baseline.

## Enum e tipi chiusi

### `RegimeType`

Valori iniziali:

- `ExpansionRiskOn`
- `InflationaryExpansion`
- `Slowdown`
- `RecessionStress`
- `Recovery`
- `UncertainTransition`
- `Goldilocks`
- `Reflation`
- `LateCycleOverheating`
- `Stagflation`
- `DeflationBust`
- `ZirpQeFinancialRepression`

### `EconomicDimension`

Valori iniziali:

- `Growth`
- `Inflation`
- `Risk`
- `Monetary`
- `Credit`
- `Liquidity`
- `Sentiment`

`Liquidity` e `Sentiment` possono non essere usate nella prima baseline, ma il modello deve poterle rappresentare.

### `FeaturePolarity`

Valori:

- `HigherIsRiskOn`
- `HigherIsRiskOff`
- `Neutral`

Sostituisce booleani ambigui come `IsHigherRiskOn`.

### `ModelRole`

Valori:

- `Baseline`
- `Challenger`
- `Retired`

## Record principali

### `MacroObservation`

Campi:

- `SeriesCode`;
- `Name`;
- `EconomicDimension`;
- `ObservationDate`;
- `PublicationDate`;
- `VintageDate`;
- `Value`;
- `Source`;
- `Unit`.

Regola:

- un'osservazione puo' essere inclusa nello snapshot solo se pubblicata/disponibile as-of.

### `MarketObservation`

Campi:

- `Symbol`;
- `Name`;
- `EconomicDimension`;
- `ObservationDate`;
- `AvailabilityDate`;
- `Value`;
- `Source`;
- `Unit`;
- `ProxyRole`.

### `DataSnapshot`

Campi:

- `AsOfDate`;
- `MacroObservations`;
- `MarketObservations`;

Responsabilita':

- rappresentare cio' che il sistema sa alla as-of date;
- non interrogare fonti esterne;
- non calcolare feature.

### `FeatureDefinition`

Campi:

- `Code`;
- `Name`;
- `EconomicDimension`;
- `FormulaDescription`;
- `Weight`;
- `Polarity`;
- `LookbackMonths`;
- `IsActive`.

### `FeatureScore`

Campi:

- `FeatureCode`;
- `Name`;
- `EconomicDimension`;
- `Weight`;
- `RawValue`;
- `NormalizedScore`;
- `ZScore`;
- `Momentum`;
- `Interpretation`.

### `FeatureSetVersion`

Campi:

- `Name`;
- `Version`;
- `FeatureDefinitions`;

### `ModelVersion`

Campi:

- `Name`;
- `Version`;
- `Role`;
- `Parameters`;
- `EffectiveFrom`;
- `Description`.

### `RegimeProbability`

Campi:

- `Regime`;
- `Probability`;
- `Rank`.

Invarianti:

- probability valida;
- rank maggiore di zero.

### `RegimeExplanation`

Campi:

- `Title`;
- `Detail`;
- `Impact`;
- `FeatureCode`;
- `Kind`.

`Kind` puo' essere:

- `Driver`;
- `ContrarySignal`;
- `Warning`;

### `RegimeSnapshot`

Output principale del detector.

Campi:

- `AsOfDate`;
- `ModelVersion`;
- `FeatureSetVersion`;
- `PrimaryRegime`;
- `OperationalRegime`;
- `Confidence`;
- `CompositeScore`;
- `Status`;
- `Probabilities`;
- `FeatureScores`;
- `Explanations`;
- `Warnings`.

Regola:

- `PrimaryRegime` e' il regime con probabilita' piu' alta;
- `OperationalRegime` puo' essere `UncertainTransition` anche se il primary e' diverso;
- `Warnings` non sono eccezioni, ma segnali di qualita' dati o copertura.

## Servizi di dominio

### `FeatureNormalizer`

Responsabilita':

- trasformare snapshot e feature definitions in feature scores;
- applicare formule baseline;
- restituire score neutrali quando una dimensione non ha dati, accompagnati da warning applicativo o explanation.

Nota:

- nella prima implementazione le formule possono essere semplici e deterministicamente codificate nel dominio, ma devono essere isolate per feature.

### `CompositeScoreCalculator`

Responsabilita':

- calcolare media pesata degli score;
- ignorare feature inattive;
- gestire peso totale zero con comportamento esplicito.

### `RegimeProbabilityNormalizer`

Responsabilita':

- normalizzare score grezzi in probabilita';
- ordinare probabilita';
- garantire somma controllata.

### `BaselineRegimeDetector`

Responsabilita':

- ricevere `DataSnapshot`, `FeatureSetVersion`, `ModelVersion`;
- calcolare feature scores;
- calcolare composite score;
- calcolare probabilita';
- decidere primary regime;
- decidere operational regime;
- costruire explanations;
- restituire `RegimeSnapshot`.

Non deve:

- leggere database;
- salvare run;
- creare versioni;
- generare report UI;
- chiamare HTTP.

### `RegimeExplanationBuilder`

Responsabilita':

- ordinare driver;
- identificare segnali contrari;
- produrre spiegazioni brevi e stabili.

## Errori e warnings

### Errori di dominio

Esempi:

- probabilita' fuori range;
- peso negativo;
- score fuori range;
- snapshot senza as-of date;
- feature definition senza codice.

Gli errori di dominio devono impedire la creazione di oggetti non validi.

### Warnings

Esempi:

- dimensione mancante;
- nessuna osservazione macro;
- nessuna osservazione market;
- feature neutrale per assenza dati;
- confidence sotto soglia.

I warnings non bloccano necessariamente il calcolo, ma possono portare a `UncertainTransition`.

## Baseline formula v0.1

Le formule iniziali possono recuperare l'intuizione del prototipo:

- `GROWTH_MOM`: produzione industriale YoY e Sahm Rule inversa.
- `INFL_PRESS`: breakeven e proxy commodity.
- `RISK_APPETITE`: VIX inverso e proxy ETF.
- `MONETARY_COND`: curva 10Y-2Y e stance monetaria.
- `CREDIT_STRESS`: HY OAS inverso e proxy credito.

Le soglie devono essere isolate in `ModelVersion.Parameters` o oggetto equivalente.

## Esempio input minimo

```text
AsOfDate: 2026-07-01
FeatureSetVersion: CRS Baseline v0.1
ModelVersion: CRS Rule-Based Engine v0.1
MacroObservations:
  INDPRO_YOY = 2.0
  SAHM = 0.22
  T10YIE = 2.2
  VIX = 16.0
  YC_10Y2Y = 0.25
  HY_OAS = 3.4
MarketObservations:
  VWCE_PROXY = 100
```

## Esempio output minimo

```text
PrimaryRegime: Goldilocks
OperationalRegime: UncertainTransition
Confidence: 0.57
CompositeScore: 0.56
Status: Transition
Probabilities:
  Goldilocks 0.34
  Reflation 0.26
  UncertainTransition 0.22
  Stagflation 0.11
  DeflationBust 0.07
Warnings:
  Confidence below confirmation threshold.
```

## Prima implementazione attesa

La prima implementazione del dominio deve includere solo:

- value object essenziali;
- enum;
- record di input/output;
- normalizer baseline;
- detector baseline;
- tests puri.

Non deve includere:

- EF Core;
- controller;
- Razor;
- import FRED;
- report HTML;
- allocation engine.
