# Macro Regime - Fase E - Slice 5: Primo challenger clustering - Done

Data: 2026-07-13

## Scopo

Introdurre il primo challenger riproducibile, confrontarlo con la baseline sugli
stessi fold e conservare anche un risultato negativo senza tuning post-hoc.

## Modello

`kmeans-recession-v1` usa k-means deterministico sulle cinque feature già
normalizzate dal runtime C#:

- `GROWTH_MOM`;
- `INFL_PRESS`;
- `RISK_APPETITE`;
- `MONETARY_COND`;
- `CREDIT_STRESS`.

La configurazione è congelata a quattro cluster. Ogni fold calcola media,
deviazione standard, centroidi e mapping cluster/NBER esclusivamente sul train.
Tra i cluster contenenti almeno un mese recessivo train viene scelto quello con
massima prevalenza Laplace-smoothed; i tie-break sono deterministici.

Il mapping rende il modello semi-supervisionato nella sola assegnazione semantica
del cluster. Il clustering delle feature resta non supervisionato.

## Anti-leakage e determinismo

Un test dedicato verifica che:

- due esecuzioni identiche producano file byte-identici;
- cambiare soltanto le label NBER nel test non modifichi le predizioni;
- il cluster selezionato contenga almeno un mese recessivo train.

Non è stato eseguito alcuno sweep di cluster, inizializzazione o mapping dopo la
lettura dei risultati reali.

## Artefatti

- configurazione: `research/regime-eval/models/kmeans-recession-v1.json`;
- config SHA-256: `a2b93379be09ed522157663b78467dcff1fe253887fc9d0beffdf5ac346b4a5c`;
- model card: `research/regime-eval/model-cards/kmeans-recession-v1.md`;
- report: `data/historical-real-2008-2025/challengers/kmeans-recession-v1-report.json`;
- report SHA-256: `2aa6e83468a22930a7c00ac2fa412be456cdb08cc7b4e082679140586c09225b`.

## Risultati OOS a date uniche

84 date, con policy first-eligible-fold:

- challenger: TP 0, FN 2, FP 0, TN 82;
- recall 0%;
- precision non definita;
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

L'accuracy del challenger è maggiore solo perché non produce mai una predizione
recessiva. È quindi una metrica ingannevole in presenza di class imbalance.

## Risultati sulle osservazioni-fold

Sulle 144 osservazioni-fold, che includono le finestre test sovrapposte:

- TP 1, FN 3, FP 9, TN 131;
- recall 25%;
- precision 10%;
- F1 14,29%;
- balanced accuracy 59,29%.

Il fold 2 intercetta un mese recessivo; il fold 3 perde il proprio mese positivo
e produce nove falsi positivi. Gli altri fold senza recessioni test non compensano
la scarsa sensibilità.

## Decisione

Il challenger non supera la baseline e non viene promosso. La model card conserva
configurazione, failure mode e raccomandazione. Modificare ora `clusterCount` o la
policy di aggregazione usando gli stessi test costituirebbe tuning post-hoc.

## Verifiche

```text
python -m unittest discover -s tests -v
python -m compileall -q regime_eval tests
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore --no-build
```

Esito:

- 10 test Python superati;
- 218 test C# superati;
- build 0 warning, 0 errori;
- nessuna modifica al detector C# o alla baseline.

## Prossimo passo

Valutare un challenger temporale HMM con nuova configurazione e nuova model card.
La persistenza dello stato può affrontare un failure mode che k-means ignora, ma
non autorizza tuning sui test già osservati.
