# Checkpoint 0052 - E12.2 corpus reale e coverage freeze

Data: 2026-07-14

## Obiettivo

Rigenerare il corpus 2008-2025 con le feature intramese E12, costruire un
dataset separato, misurare la copertura totale e per fold e congelare tutti gli
input prima di definire formule o soglie dei candidati.

## Realizzato

- creato il layout locale isolato
  `data/historical-real-v12-2008-2025/`, senza modificare v1.1;
- corretta l'integrazione SAHM: `UNRATE` resta ALFRED initial-release, mentre
  `SAHMREALTIME`, che FRED non espone come serie ALFRED, usa la storia FRED e
  riempie soltanto i buchi non ricostruibili;
- popolati 213 snapshot macro e 4.536 snapshot market;
- costruito dataset schema v1 con 213 righe e 3.834 forward return;
- validazione point-in-time superata e piano rolling 10/2/1 con 6 fold;
- implementato `e12-freeze-foundation`, report write-once che controlla
  coerenza corpus/dataset, misura ogni input per train/test e lega tutti gli
  artefatti tramite SHA-256;
- versionato `e12-data-foundation-lock-v1.json`, così i candidati futuri
  possono riferire il freeze anche se `data/` resta esclusa da Git.

## Copertura osservata

| Feature | Righe | Copertura | Prima data |
|---|---:|---:|---|
| `VIX_MONTHLY_MAX` | 213/213 | 100% | 2008-04-30 |
| `SPY_MONTHLY_MAX_DRAWDOWN` | 213/213 | 100% | 2008-04-30 |
| `HYG_MONTHLY_MAX_DRAWDOWN` | 213/213 | 100% | 2008-04-30 |
| `SOFR_EFFR_MONTHLY_MAX` | 93/213 | 43,661972% | 2018-04-30 |

Tutti i test set dei sei fold hanno copertura SOFR-EFFR del 100%. I train set
passano da 0%, 10%, 20%, 30,252101%, 40,495868% a 50,413223%. Questo dato non
autorizza a eliminare fold: E12.3 deve preregistrare una gestione missing-aware
o rendere esplicitamente opzionale il canale funding, prima della valutazione.

## Controlli sugli episodi

- settembre 2019: VIX month-end `16,24`, massimo mensile `19,66`, massimo
  SOFR-EFFR `295 bp`; lo shock repo ora e' visibile;
- marzo 2020: VIX month-end `53,54`, massimo `82,69`, drawdown SPY `28,319062%`
  e HYG `21,223605%`.

## Freeze

- freeze id: `15eef71e961b3dd01f2dbf88`;
- dataset SHA-256:
  `4b42c41c875dc8cb19168c6529fd935017120da6640d605da99c64a5eeaad30f`;
- foundation report SHA-256:
  `712454f92299278318055a813685426c15a31e015c018630d274fa3c2a13cef9`;
- corpus aggregate SHA-256:
  `e96ebb8003dc3dcc9729065cb85a915b91300847508185d7f82da5e3ea872dfb`.

## Decisione

E12.2 congela esclusivamente il dato. Non sono stati eseguiti, classificati o
promossi candidati e l'outer OOS non e' stato usato per selezione. Il prossimo
step consentito e' congelare formula e gate inner-only di
`event-aware-financial-stress-v1`.

## Verifica

- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 37/37 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- `git diff --check`: superato;
- hash del lock confrontati con gli artefatti locali: coerenti.
