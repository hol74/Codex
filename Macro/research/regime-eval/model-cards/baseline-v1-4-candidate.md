# Model card - Baseline v1.4 candidate

Data: 2026-07-13.

## Stato

Supera train gate v2 e audit OOS E6. Diventa baseline di riferimento per la
ricerca successiva, ma non e' promossa come modello operativo: il benchmark
2008-2025 e' stato usato durante lo sviluppo e non sostituisce holdout fresco o
shadow-live.

## Modifiche preregistrate

La v1.4 conserva feature e mapping VIX v1.3 e modifica la geometria:

- target risk degli archetipi tradotti preservando gli stessi livelli VIX
  impliciti nella v1.2;
- soglia risk della regola divergente tradotta da score 0,40 / VIX 28,8 a
  score logistico 0,22146613;
- probabilita' ancora basate sul fit quadratico;
- confidence separata dallo score power: 75% fit non potenziato e 25%
  separazione relativa fra i primi due archetipi;
- threshold 0,55 e penalita' missing/divergence invariati.

Configurazione: `models/baseline-v1-4-preregistered.json`.

## Train gate v2

Sulle 84 date inner-validation uniche:

- feature integrity: superata;
- regime coverage: superata, 4 regimi e Goldilocks 61,90%;
- operational robustness: 6 fold su 6;
- `UncertainTransition`: 2,38%;
- tutte le boundary rate sotto il 25%.

## OOS autorizzato

84 date uniche, 2018-04-30 / 2025-03-31:

- audit: superato, zero violazioni;
- confidence media 0,7045, mediana 0,7044;
- `UncertainTransition`: 2,38%;
- primary: Goldilocks 47,62%, Reflation 39,29%, DeflationBust 11,90%,
  LateCycleOverheating 1,19%;
- transition rate operativo: 24,10%;
- boundary rate massimo: growth 16,67%; `RISK_APPETITE` 1,19%.

## Ground truth NBER

Sui soli due mesi recessivi OOS:

- recall 100%;
- precision 20%;
- F1 33,33%;
- balanced accuracy 95,12%;
- 8 falsi positivi, concentrati fra maggio 2020 e febbraio 2021.

Il recall e' positivo, ma precision e F1 regrediscono rispetto al segnale
operational v1.1. Il campione NBER e' troppo piccolo e binario per validare la
tassonomia multiregime.

## Stress non recessivi

La cronologia multi-label v1 aggiunge 6 episodi non sovrapposti a recessioni
NBER. Sulle date OOS, la baseline non allinea nessuno dei 6 mesi di stress
finanziario e nessuno dei 3 mesi di growth scare; inflation shock e monetary
tightening hanno allineamento primary rispettivamente 3,85% e 5,00%.

Il risultato e' negativo e non viene usato per cambiare la v1.4. Indica un
blind spot concreto sugli stress finanziari non recessivi e, per le label
inflazione/tightening, anche il limite di una corrispondenza diretta fra singola
dimensione e regime composito.

## Decisione

La v1.4 chiude il gate tecnico E6 e diventa il benchmark rule-based per i nuovi
challenger. Non autorizza allocazione reale automatica. Prima di qualunque
promozione servono una serie shadow-live 2026+, un contratto stress dimensionale
validato su episodi nuovi e confronto challenger senza riutilizzare l'OOS per
ulteriore tuning della v1.4.
