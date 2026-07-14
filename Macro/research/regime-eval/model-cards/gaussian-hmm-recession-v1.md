# Model card - gaussian-hmm-recession-v1

Data valutazione: 2026-07-13.

Stato: challenger temporale conservato, non promosso.

Raccomandazione: mantenere la baseline di ricerca v1.4; non eseguire tuning
post-hoc di questo HMM sul benchmark gia' osservato.

## Scopo

Valutare se un Gaussian Hidden Markov Model a tre stati, grazie alla persistenza
temporale, migliori il riconoscimento dei mesi recessivi rispetto alla baseline
rule-based v1.4. Il modello produce una classificazione binaria dopo un mapping
train-only degli stati latenti; non sostituisce la tassonomia macro completa.

## Configurazione congelata

- modello: Gaussian HMM con emissioni diagonali e 3 stati;
- feature: `GROWTH_MOM`, `INFL_PRESS`, `RISK_APPETITE`, `MONETARY_COND`,
  `CREDIT_STRESS`;
- standardizzazione: media e deviazione standard del solo train;
- stima: Baum-Welch in log-space, massimo 100 iterazioni, tolleranza `1e-6`;
- inizializzazione: k-means deterministico farthest-first sul train;
- variance floor `0.05`; transition pseudo-count `1.0`;
- mapping recessivo: massima prevalenza NBER Laplace-smoothed sul solo train;
- test: posterior filtrato causalmente dal posterior train finale, senza
  backward smoothing;
- date test sovrapposte: vale il primo fold eleggibile.

Config SHA-256:
`75ffe4bcb3a5e21e506740f85a0ec45c2a412dd459196f715298f6929938f404`.

## Dati e protocollo

- baseline: `1.4-candidate`, SHA-256
  `643eaafc9cc30ac8beb1358ccea564afe8eca5d2622605a5335b95c75b8de0f8`;
- dataset: 2008-04-30 / 2025-12-31, 213 righe;
- walk-forward: train 10 anni, test 2 anni, step 1 anno;
- 6 fold, 144 osservazioni test-fold, 84 date OOS uniche;
- ground truth: NBER US recessions v1;
- scaling, parametri e mapping stato-label sono rifatti in ogni train fold;
- tutti i fold convergono, fra 14 e 33 iterazioni;
- i test verificano output byte-identico, indipendenza dalle label test e
  assenza di influenza di un dato futuro su una predizione precedente.

Il benchmark 2008-2025 e' development/validation gia' osservato, non un holdout
finale incontaminato.

## Risultati OOS a date uniche

Challenger HMM:

- TP 1, FN 1, FP 14, TN 68;
- recall 50%; precision 6,67%; specificity 82,93%;
- F1 11,76%; balanced accuracy 66,46%; accuracy 82,14%;
- falso negativo: 2020-03-31.

Baseline v1.4 operational:

- TP 2, FN 0, FP 8, TN 74;
- recall 100%; precision 20%; specificity 90,24%;
- F1 33,33%; balanced accuracy 95,12%; accuracy 90,48%.

Delta HMM meno baseline: recall -50 punti percentuali, precision -13,33,
specificity -7,32, F1 -21,57, balanced accuracy -28,66; 6 falsi positivi e un
falso negativo in piu'.

## Failure mode

Il modello intercetta aprile 2020 ma perde marzo 2020 e prolunga lo stato
recessivo fino a marzo 2021. Produce inoltre una falsa sequenza positiva tra
febbraio e aprile 2022. La persistenza riduce la reattivita' all'inizio dello
shock e rende troppo lenta l'uscita dallo stato associato alla recessione.

La scarsita' di mesi recessivi nel train rende fragile il mapping fra stato
latente e label NBER; stati e mapping cambiano tra fold. La convergenza numerica
non implica efficacia predittiva.

## Decisione Model Gate

Gate automatico fallito per `RECALL_REGRESSION` e `F1_REGRESSION`. Il challenger
non entra nel runtime e non sostituisce la baseline v1.4.

Non si modificano numero di stati, floor, prior, mapping o aggregazione dopo la
lettura OOS. Una nuova ipotesi richiede nuovo model id, preregistrazione e,
preferibilmente, dati freschi o una ground truth di stress piu' ricca.

## Artefatti

- configurazione: `research/regime-eval/models/gaussian-hmm-recession-v1.json`;
- report locale:
  `data/historical-real-v11-2008-2025/challengers/gaussian-hmm-recession-v1-report.json`;
- report SHA-256:
  `df07f9bff006f00bbd8e72b129dc869360f83e72c38392850e18611556e3200e`;
- dataset SHA-256:
  `1a2db1c7540a2419757b37d01717de258548f9bcf301994dfcd5c83f47f17649`;
- ground truth SHA-256:
  `082148d66b47f55ae6e519822b1fbbfe7331604ce86388a1dd8ab60b5148effa`.
