# Macro Regime - Fase E - Slice 7: Gaussian HMM v1 rejected

Data di chiusura: 2026-07-13.

## Esito

Il primo challenger temporale e' stato preregistrato, implementato ed eseguito
contro la baseline di ricerca v1.4. Il Gaussian HMM converge in tutti i fold ma
fallisce il Model Gate per regressione di recall e F1. Non viene promosso e non
viene ritoccato sullo stesso OOS.

## Incremento implementato

- configurazione congelata `gaussian-hmm-recession-v1`;
- HMM gaussiano a tre stati con covarianza diagonale;
- Baum-Welch deterministico in log-space;
- standardizzazione, stima e mapping stato/NBER solo sul train;
- inferenza test filtrata causalmente, senza backward smoothing;
- aggregazione delle date sovrapposte con earliest eligible fold;
- confronto automatico con primary e operational della v1.4;
- comando CLI `hmm-report` e report JSON legato agli hash degli input;
- test di determinismo, isolamento delle label test e non anticipazione.

## Risultato reale

Copertura: 6 fold, 144 osservazioni-fold, 84 date OOS uniche dal 2018-04-30 al
2025-03-31. Tutti i fold convergono in 14-33 iterazioni.

HMM: TP 1, FN 1, FP 14, TN 68; recall 50%, precision 6,67%, F1 11,76%, balanced
accuracy 66,46%.

Baseline v1.4 operational: TP 2, FN 0, FP 8, TN 74; recall 100%, precision 20%,
F1 33,33%, balanced accuracy 95,12%.

Il challenger perde marzo 2020, prolunga troppo lo stato recessivo dopo aprile
2020 e genera una seconda sequenza falsa nel 2022. Le violazioni automatiche
sono `RECALL_REGRESSION` e `F1_REGRESSION`.

## Decisione

Risultato negativo valido e riproducibile. La baseline v1.4 resta il riferimento
di ricerca. Non si apre una variante HMM v1.1 scegliendo parametri sullo stesso
benchmark. Il prossimo incremento deve dare priorita' allo shadow-live 2026+ e
alla ground truth degli stress non recessivi; un modello temporalmente diverso
richiedera' una nuova preregistrazione.

## Verifiche

- tutti i fold HMM convergenti;
- output funzione/CLI byte-identico;
- cambiare le sole label test non cambia le predizioni;
- cambiare l'ultima osservazione test non cambia la prima predizione test;
- report SHA-256:
  `df07f9bff006f00bbd8e72b129dc869360f83e72c38392850e18611556e3200e`.

- build: 0 warning, 0 errori;
- test C#: 237 superati (Domain 93, Application 30, Infrastructure 87,
  Reporting 2, CLI 19, Web 6);
- test Python: 14 superati; compileall superato;
- `git diff --check`: superato.
