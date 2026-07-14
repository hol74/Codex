# Checkpoint 0053 - E12.3 event-aware financial stress

Data: 2026-07-14

## Obiettivo

Preregistrare ed eseguire un candidato task-specifico per stress finanziario,
usando il foundation lock E12.2 senza aprire l'outer OOS.

## Realizzato

- congelata la configurazione `event-aware-financial-stress-v1`;
- congelato il gate `e12-financial-stress-gate-v1`;
- creato un manifest write-once che lega candidato, gate e foundation lock;
- implementato un segnale causale e stateless su VIX massimo, drawdown SPY/HYG,
  HY proxy e overlay SOFR-EFFR;
- mantenuto il funding mancante come `null`: nessun backfill, zero-fill o
  imputazione fitted;
- separate le metriche sulla classification universe curata dal generico
  insieme dei mesi non etichettati;
- prodotte probabilita' prima di collegare le label;
- usate 84 date inner uniche su 6 fold e zero righe outer-test.

## Esito

Il candidato intercetta lo shock repo protetto e passa 8 controlli su 10, ma
fallisce due requisiti congiuntivi:

- recall `0,28571429`, sotto il minimo `0,50`;
- average precision `0,46610797`, sotto il minimo `0,50`.

F1 `0,4`, Brier `0,17646004`, ECE `0,17392527` e longest alert run di 3 mesi
passano il gate. Il repricing 2018 Q4 e' intercettato a livello episodio; lo
stress bancario regionale 2023 e' perso. Esito finale:
`REJECTED_FOR_SHADOW`.

## Artefatti

- config SHA-256:
  `5da979a17fb7a346752a8b35698b45b5da222a0290f44055b46da73519e50ab7`;
- gate SHA-256:
  `e63b9265d1066659f27c2f620b51deb28563bbb36411a14845b1c7f0f16bf6f2`;
- preregistration SHA-256:
  `884cd80566dd02a006257a874c91883f23a669614f486097781f15b601e10e18`;
- report SHA-256:
  `adf2939eac5af5223aea312393409c96c5da4a060325e75f5b1f85cb58002174`.

## Decisione

Nessun tuning post-hoc e nessuna promozione. E12.3 e' chiusa come esperimento
negativo utile: le feature risolvono il blind spot repo, ma la formula v1 non
generalizza abbastanza agli altri episodi. Il prossimo incremento previsto dal
piano e' E12.4, `sahm-yield-hazard-v1`, con task e gate recessivi separati.

## Verifica

- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 40/40 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- `git diff --check`: superato;
- test dedicati: funding mancante non imputato, overlay repo attivo, input base
  obbligatori e preregistrazione write-once.
