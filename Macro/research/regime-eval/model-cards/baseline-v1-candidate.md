# Model card - Baseline v1 candidate

Data valutazione: 2026-07-13.

## Stato

Research candidate non promossa. Il gate E6 resta negativo. La baseline runtime
e la `0.1-demo` non sono state sostituite.

## Scopo

Correggere tre difetti semantici osservati nella `0.1-demo` senza introdurre
tuning sui fold test:

- trattare `HY_OAS` storico per cio' che contiene realmente, cioe' il proxy
  `BAA10Y`, con scala 1%-4%;
- evitare che una curva molto ripida sia sempre interpretata come favorevole;
- rendere piu' sensibile il breakeven decennale, dichiarando che non sostituisce
  l'inflazione realizzata.

## Versioni

- feature set: `CRS Research Baseline / 1.0-candidate`;
- modello: `CRS Rule-Based Research Candidate / 1.0-candidate`;
- effective date: 2026-07-13;
- formula dei raw regime score: invariata rispetto alla demo;
- confirmation threshold: 0,55, invariata per evitare tuning post-hoc.

## Risultati OOS unici

Campione: 84 date, 2018-04-30 - 2025-03-31.

Miglioramenti rispetto alla demo:

- saturazione `CREDIT_STRESS`: da 95,24% a 1,19%;
- regimi primari osservati: da 2 a 3;
- Goldilocks dominante: da 94,05% a 83,33%;
- due gate E6 su quattro precedentemente falliti sono ora superati.

Regressioni e gate ancora falliti:

- `UncertainTransition`: da 57,14% a 78,57%;
- Goldilocks 83,33%, ancora oltre il limite dell'80%;
- confidenza media: 0,5028;
- segnale recessivo primary: recall 100%, precision 16,67%, F1 28,57%;
- segnale recessivo operational: recall 100%, precision 22,22%, F1 36,36%.

La candidate intercetta marzo-aprile 2020, ma produce piu' falsi positivi
post-shock. La ground truth contiene un solo episodio recessivo OOS e non misura
la qualita' degli altri regimi.

## Decisione

Non promuovere e non abbassare la soglia di conferma dopo avere osservato questi
risultati. Il prossimo cambiamento deve essere una nuova versione preregistrata,
orientata a:

1. integrare inflazione realizzata e momentum;
2. distinguere inversione e re-steepening usando dinamica temporale;
3. rivedere confidence e superficie dei raw score su train/nested validation,
   non sui mesi OOS gia' osservati;
4. estendere lo storico macro e riservare un holdout fresco/shadow-live.

## Artefatti locali

Gli artefatti sono sotto `data/historical-real-2008-2025/baseline/`, esclusi da
Git: evaluation v1, walk-forward report, NBER report e audit report. Ogni report
contiene gli hash degli input.
