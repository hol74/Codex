# Model Card - kmeans-recession-v1

Data valutazione: 2026-07-13

Stato: challenger conservato, non promosso.

Raccomandazione: non promuovere al runtime o a baseline primaria.

## Scopo

Primo challenger minimale per verificare se un clustering deterministico delle
cinque feature normalizzate separa i mesi recessivi NBER senza replicare le regole
del `BaselineRegimeDetector`.

Il modello non produce la tassonomia macro completa. Esegue solo classificazione
binaria recessione/non recessione dopo un mapping train-only dei cluster.

## Configurazione congelata

- modello: k-means deterministico;
- feature: `GROWTH_MOM`, `INFL_PRESS`, `RISK_APPETITE`, `MONETARY_COND`,
  `CREDIT_STRESS`;
- cluster: 4;
- scaling: media e deviazione standard della sola finestra train;
- inizializzazione: punto più vicino alla media, poi farthest-first;
- massimo 100 iterazioni, tolleranza `1e-10`;
- mapping recessivo: tra i cluster train contenenti almeno un mese NBER positivo,
  selezione della massima prevalenza recessiva Laplace-smoothed;
- nessun hyperparameter sweep;
- date test sovrapposte: vale la predizione del primo fold eleggibile.

Config SHA-256:
`a2b93379be09ed522157663b78467dcff1fe253887fc9d0beffdf5ac346b4a5c`.

## Dati e protocollo

- dataset: 2008-04-30 / 2025-12-31, 213 righe;
- walk-forward: train 10 anni, test 2 anni, step 1 anno;
- fold: 6;
- osservazioni test-fold: 144;
- date OOS uniche: 84;
- ground truth: NBER US recessions v1;
- fitting, scaling e mapping cluster-label usano solo il train;
- un test automatico verifica che cambiare esclusivamente le label test non
  modifichi le predizioni.

Le feature derivano dalla baseline retrospettiva `0.1-demo`; il challenger non è
quindi indipendente dalla sua feature engineering.

## Risultati OOS a date uniche

Challenger:

- TP 0, FN 2, FP 0, TN 82;
- recall 0%;
- precision non definita, perché non esistono predizioni positive;
- specificity 100%;
- F1 0%;
- balanced accuracy 50%;
- accuracy 97,62%.

Baseline primary sullo stesso campione:

- TP 2, FN 0, FP 3, TN 79;
- recall 100%;
- precision 40%;
- F1 57,14%;
- balanced accuracy 98,17%;
- accuracy 96,43%.

L'accuracy più alta del challenger è un artefatto dello sbilanciamento: il modello
non riconosce nessuno dei due mesi recessivi. Rispetto alla baseline perde 100
punti percentuali di recall e 57,14 punti di F1.

## Risultati sulle osservazioni-fold

Considerando anche la duplicazione dovuta ai test biennali sovrapposti:

- TP 1, FN 3, FP 9, TN 131;
- recall 25%;
- precision 10%;
- F1 14,29%;
- balanced accuracy 59,29%.

Il fold 2 rileva un mese recessivo; il fold 3 ne perde uno e produce nove falsi
positivi. Questa instabilità conferma che pochi mesi recessivi nel train non
permettono un mapping robusto cluster-label.

## Failure mode

- cluster non stabili semanticamente tra fold;
- mapping train NBER fragile con 1-3 mesi recessivi in cinque dei sei fold;
- nessuna persistenza temporale nel k-means;
- distanza euclidea e cluster sferici non rappresentano transizioni di regime;
- classe recessiva estremamente rara;
- earliest-fold aggregation può privilegiare un modello addestrato su una storia
  più vecchia, ma la policy era fissata prima dell'esecuzione.

## Decisione Model Gate

Il challenger non supera il confronto minimo con la baseline e non è candidato
alla promozione. Codice, configurazione, test e report vengono conservati come
risultato negativo riproducibile.

Non si esegue tuning post-hoc su numero cluster, mapping o aggregazione usando
queste finestre test. Una nuova ipotesi richiede un nuovo model id e una nuova
model card.

## Artefatti

- configurazione: `research/regime-eval/models/kmeans-recession-v1.json`;
- report locale: `data/historical-real-2008-2025/challengers/kmeans-recession-v1-report.json`;
- report SHA-256:
  `2aa6e83468a22930a7c00ac2fa412be456cdb08cc7b4e082679140586c09225b`;
- ground truth SHA-256:
  `082148d66b47f55ae6e519822b1fbbfe7331604ce86388a1dd8ab60b5148effa`;
- dataset SHA-256:
  `3cac7d9b290b149f6529fea80e326ff83f8e44abaf907eb91fb4a368099a288a`.
