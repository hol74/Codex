# Macro Regime - Fase E10: Model Evidence v2 e dual-timescale

Data di chiusura tecnica: 2026-07-14.

## Scopo

Separare gate tecnico e promozione operativa, introdurre una valutazione
dimensionale degli stress e testare una nuova ipotesi a due scale temporali
senza modificare baseline o challenger gia' osservati.

## Piano eseguito

1. La v1.4 resta `research-baseline`; k-means v1 e Gaussian HMM v1 restano
   respinti e immutati.
2. Implementato `model-evidence-and-promotion-v2` con lifecycle distinti,
   `INSUFFICIENT_EVIDENCE`, metriche probabilistiche, calibration table,
   average precision, bootstrap circolare a blocchi e diagnostica temporale.
3. Versionato `us-non-recession-stress-v2.json`, con dimensioni esplicite e
   partizioni `development-v1` / `protected-v2`.
4. Preregistrato e implementato `dual-timescale-regime-v1`, causale e senza
   fitting sulle label.
5. Eseguiti una sola volta i tre report reali autorizzati e conservati anche i
   risultati negativi.
6. Il primo ciclo E9 `full` del 2026-07-31 resta temporalmente non eleggibile
   fino alla chiusura del mese e alla disponibilita' point-in-time dei dati.

## Baseline v1.4 - Evidence v2

Su 84 date OOS uniche:

- 2 mesi positivi, 82 negativi, un solo episodio recessivo;
- TP 2, FN 0, FP 8, TN 74;
- recall 100%, precision 20%, F1 33,33%;
- average precision 0,29166667;
- Brier score 0,03204335; log loss 0,16986169;
- expected calibration error descrittivo 0,11240705;
- massimo run di falsi positivi: 6 mesi;
- primo segnale di uscita dopo il trough COVID: novembre 2020, lag 7 mesi.

Il gate restituisce `INSUFFICIENT_EVIDENCE`: falliscono il minimo di 12 mesi
positivi, 2 episodi positivi e il requisito di evidenza prospettica fresca.
L'operational promotion e' bloccata.

Report locale SHA-256:
`ef24dec3116987630ddb98ba39208844f3a99b3a173af65d4671cb7f295b28db`.

## Stress contract v2

La dimensione migliora l'osservabilita' rispetto al mapping diretto sul regime,
ma non risolve il problema:

- full dataset financial stress: 57,14% dimensionale contro 14,29% regime;
- growth scare: 0% dimensionale;
- inflation shock: 38,46% dimensionale contro 3,85% regime;
- monetary tightening: 40,91% dimensionale contro 13,64% regime;
- partizione protetta: financial stress 0% su taper 2013/repo 2019;
- taper 2013: monetary restriction 100% sui due mesi.

Il risultato segnala che alcune trasformazioni dimensionali sono informative,
ma `RISK_APPETITE`/`CREDIT_STRESS` non rappresentano bene funding stress e shock
di mercato non recessivi.

Report locale SHA-256:
`8412f3c7612efabf6d63c3a393e7bb141a31da30a5867c21c02b0fb391b35ea7`.

## Dual-timescale v1

Su 84 date OOS uniche:

- TP 0, FN 2, FP 13, TN 69;
- recall 0%, precision 0%, F1 0%, balanced accuracy 42,07%;
- Brier score 0,15131507; log loss 0,48335593;
- delta vs baseline: recall -100 punti, F1 -33,33, 5 FP e 2 FN in piu';
- perde marzo e aprile 2020;
- resta falsamente positivo da maggio 2020 a maggio 2021;
- financial stress protetto v2: 0%.

Il modello e' respinto. L'ipotesi a due scale identifica una giusta separazione
concettuale, ma combinazione geometrica e isteresi v1 non risolvono onset e
durata. Alpha, pesi e soglie non vengono modificati sul benchmark osservato.

Report locale SHA-256:
`2aa18e680f134f2b1a9586ac20dea879bce8e11604b9dc2dd9f50dc66ceaa899`.

## Implementazione

- `regime_eval/evidence.py`;
- `regime_eval/dimensions.py`;
- `regime_eval/dual_timescale_challenger.py`;
- metriche probabilistiche condivise in `regime_eval/metrics.py`;
- comandi CLI `evidence-report` e `dual-timescale-report`;
- stress report compatibile con schema v1 e v2;
- configurazioni e model card preregistrate/versionate.

## Verifiche

- build .NET: 0 warning, 0 errori;
- test C#: 240 superati;
- test Python: 28 superati;
- `python -m compileall`: superato;
- `git diff --check`: superato, salvo warning informativi sui line ending;
- nuovi test: determinismo, label independence, causalita' futura, partizioni
  stress e blocco della promozione per evidenza insufficiente.

## Decisione e prossimo passo

E10 e' tecnicamente completata con esito di modello negativo. Non serve un
quarto tuning sul 2008-2025. Il prossimo passo operativo resta il ciclo E9
`full` del cutoff 2026-07-31 quando diventa eleggibile. In parallelo si puo'
progettare, ma non selezionare sul vecchio OOS, una nuova ipotesi con change-point
causale, durata esplicita e nuove osservabili di funding/financial stress.
