# Checkpoint 0049 - E11.2 baseline dimensionale v1.5

Data: 2026-07-14

## Obiettivo

Implementare la candidate `baseline-v1-5-dimensional` preregistrata in E11.1,
verificarne causalita' e scenari archetipici ed eseguire esclusivamente il gate
inner-validation, mantenendo chiuso l'outer OOS.

## Realizzato

- aggiunto `regime_eval.dimensional_baseline`;
- implementati impulsi causali mensili di financial stress e growth
  deterioration con primo impulso nullo;
- riusate senza modifica geometria, score power, confidence, confirmation e
  divergence policy v1.4;
- aggiunti cinque scenari archetipici deterministici;
- implementato il comando `e11-dimensional-baseline-gate`;
- vincolati gate, candidate config e input al manifest write-once E11.1;
- usate soltanto code inner-validation degli outer train, con zero righe dei
  corrispondenti outer test;
- aggiunti test di causalita', determinismo, archetipi e rifiuto di un gate
  alterato.

## Esito inner-only

La candidate conserva le metriche binarie della v1.4 sulle 84 date uniche:
recall `1,0`, F1 `0,33333333`, 2 true positive e 8 false positive. Average
precision migliora da `0,29166667` a `0,41666667`.

Il gate fallisce due requisiti congiuntivi:

- Brier score `0,0344838` contro `0,03366408`, delta `+0,00081972`;
- protected stress dimension hit rate `0/2` sui mesi repo settembre-ottobre
  2019.

Esito finale: `REJECTED_FOR_SHADOW`. Non sono stati modificati parametri e non
e' stata eseguita alcuna diagnostica outer OOS.

## Artefatto

- report runtime:
  `data/historical-real-v11-2008-2025/challengers/baseline-v1-5-dimensional-inner-gate.json`;
- SHA-256:
  `02ac093bbad8159b9f90941bd1307877ecec7c0a788c34b6913bed39ca2961a1`.

## Verifica

- `python -m compileall -q regime_eval tests`: superato;
- `python -m unittest discover -s tests -v`: 32/32 test superati;
- `dotnet build MacroRegime.slnx --no-restore`: superata, 0 warning e 0 errori;
- `dotnet test MacroRegime.slnx --no-restore --no-build`: 240/240 test superati;
- `git diff --check`: superato.

Il prossimo incremento e' E11.3, implementazione dei challenger
changepoint-duration v1 e rare-event-logit v1.
