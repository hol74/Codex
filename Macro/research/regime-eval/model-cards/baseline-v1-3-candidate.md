# Model card - Baseline v1.3 candidate

Data: 2026-07-13.

## Stato

Respinta dal train gate v2. Nessun report OOS, audit OOS o confronto NBER e'
stato aperto.

## Modifica preregistrata

La v1.3 modifica esclusivamente `RISK_APPETITE`:

```text
score = 1 / (1 + exp((VIX - 20) / 7))
```

La trasformazione inversa logistica e' continua e non applica hard clipping.
Feature temporali, archetipi, score power, confidence, penalita' e threshold
restano identici alla v1.2. La configurazione congelata e'
`models/baseline-v1-3-preregistered.json`.

## Train gate v2

Sulle 84 date inner-validation uniche, 2016-05-31 / 2023-04-28:

- integrita' feature superata;
- `RISK_APPETITE` boundary rate 1,19%, contro 27,38% della v1.2;
- copertura superata: 4 regimi, Goldilocks dominante al 53,57%;
- robustezza operativa fallita: 2 fold validi su 6, minimo 4;
- `UncertainTransition` aggregato 60,71%.

Quote di incertezza per fold: 47,83%, 21,74%, 58,33%, 66,67%, 60% e 76%.

## Decisione

La trasformazione VIX raggiunge il suo obiettivo locale, ma non e' compatibile
con gli archetipi/confidence congelati: la diversa scala riduce fit e margini e
peggiora la conferma operativa. La v1.3 non e' promossa e non si abbassa la
soglia.

Il prossimo incremento deve trattare congiuntamente scala delle feature,
coordinate degli archetipi e confidence usando soltanto inner fit/validation.
Richiede una nuova versione; v1.3 resta immutata come risultato negativo.
