# Macro Regime - Fase E - Slice 4: Ground truth recessiva NBER - Done

Data: 2026-07-13

## Scopo

Introdurre una label recessiva esterna, versionata e non circolare per misurare
la capacità della baseline di identificare `DeflationBust`, mantenendo separati
input del detector e ground truth di valutazione.

## Fonte e convenzione

La cronologia usa i turning point ufficiali NBER e il cross-check mensile FRED
`USREC`:

- Great Recession: peak dicembre 2007, trough giugno 2009;
- COVID-19 recession: peak febbraio 2020, trough aprile 2020.

Per convenzione NBER il peak month è l'ultimo mese dell'espansione e il trough è
l'ultimo mese della recessione. Le label positive sono quindi gennaio 2008 /
giugno 2009 e marzo / aprile 2020.

Fonti ufficiali:

- https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions
- https://www.nber.org/research/business-cycle-dating
- https://fred.stlouisfed.org/series/USREC

La ground truth è congelata in
`research/regime-eval/ground-truth/nber-us-recessions-v1.json`; ogni estensione
futura richiede una nuova versione.

## Implementazione

Il comando Python `recession-report`:

- valida schema, periodi non sovrapposti e regola mese-dopo-peak;
- verifica che la copertura contenga tutto il dataset;
- collega dataset, evaluation, walk-forward plan e ground truth tramite SHA-256;
- misura separatamente `primaryRegime == DeflationBust` e
  `operationalRegime == DeflationBust`;
- salva confusion matrix, recall/FNR, specificity/FPR, precision, accuracy,
  balanced accuracy, F1, date false positive/negative e detection lag;
- usa ogni data test una sola volta nell'aggregato, conservando anche i sei fold.

`UncertainTransition` non è trattato come recessione confermata; la sua presenza
nei mesi recessivi viene conteggiata separatamente.

## Artefatti

- ground truth SHA-256: `082148d66b47f55ae6e519822b1fbbfe7331604ce86388a1dd8ab60b5148effa`;
- report reale: `data/historical-real-2008-2025/baseline/baseline-nber-recession-report.json`;
- report SHA-256: `f375c300ba0463e116fef5e89c654db3477811c158e41b38a98ee3bff793c5e6`;
- dataset SHA-256: `3cac7d9b290b149f6529fea80e326ff83f8e44abaf907eb91fb4a368099a288a`.

Il report reale resta sotto `data/` ed è escluso da Git; la ground truth e il
codice di scoring sono versionati.

## Risultati out-of-sample

Unione delle date test: 84 righe, 2018-04-30 / 2025-03-31.

- mesi recessivi: 2 (2,38%);
- true positive: 2;
- false negative: 0;
- false positive: 3 (`2020-05-29`, `2020-06-30`, `2020-10-30`);
- true negative: 79;
- recall: 100%;
- precision: 40%;
- specificity: 96,34%;
- F1: 57,14%;
- balanced accuracy: 98,17%.

Primary e operational coincidono su questa finestra. L'accuracy del 96,43% è
dominata dalla classe non recessiva e non costituisce da sola un risultato forte:
sono presenti soltanto due label positive, entrambe nella stessa recessione.

## Risultati sul periodo completo

Sulle 213 righe, 17 sono recessive.

Primary `DeflationBust`:

- TP 12, FN 5, FP 3, TN 193;
- recall 70,59%, precision 80%, specificity 98,47%;
- F1 75%, balanced accuracy 84,53%.

Operational `DeflationBust`:

- TP 10, FN 7, FP 3, TN 193;
- recall 58,82%, precision 76,92%, specificity 98,47%;
- F1 66,67%, balanced accuracy 78,65%.

La Great Recession è segnalata per la prima volta a settembre 2008, cinque mesi
dopo il primo sample disponibile di aprile. Le date aprile-agosto 2008 sono false
negative per primary e operational; maggio-giugno 2009 diventano ulteriori false
negative operative perché il detector passa a `UncertainTransition`.

La recessione COVID è intercettata a marzo 2020 senza lag mensile; i segnali di
maggio, giugno e ottobre 2020 sono false positive rispetto alla label NBER, pur
potendo rappresentare stress macro successivo alla recessione ufficiale.

## Limiti

- NBER è una cronologia ex-post, annunciata con ritardo: non è un input real-time.
- La label binaria US non valida `Goldilocks`, `Stagflation`, `Reflation` o altri
  regimi della tassonomia.
- Due soli mesi recessivi OOS non bastano per conclusioni robuste.
- I fold test si sovrappongono; per questo l'aggregato deduplica le date.
- La baseline 0.1-demo è efficace dal 2026: anche questa valutazione è
  retrospettiva e non una performance live storica.

## Verifiche

```text
python -m unittest discover -s tests -v
python -m compileall -q regime_eval tests
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore --no-build
```

Esito atteso e verificato:

- 9 test Python superati;
- 218 test C# superati;
- build 0 warning, 0 errori;
- nessuna modifica al detector o alle sue soglie.

## Prossimo passo

Introdurre un primo challenger minimale con configurazione e model card, eseguito
sugli stessi fold e confrontato contro baseline e ground truth NBER. Nessun tuning
può usare le finestre test; i risultati negativi devono essere conservati.
