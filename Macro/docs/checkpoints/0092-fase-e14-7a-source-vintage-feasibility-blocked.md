# Checkpoint 0092 - E14.7a source/vintage feasibility blocked

Data: 2026-07-15

## Obiettivo

Verificare accessibilita', licenza, copertura episodio, vintage/release
semantics e break metodologici delle fonti E14.7 senza acquisire osservazioni.

## Realizzato

- aggiunti evidence schema, evidence pack e contratto hash-bound E14.7a;
- aggiunto il comando `e14-audit-source-vintage-feasibility`;
- classificata ogni fonte e ogni famiglia come `ready`, `conditional` o
  `blocked`;
- misurati per ogni famiglia e episodio i mesi causali disponibili rispetto al
  minimo preregistrato;
- applicati in modo bloccante licenze, copertura componente e storia causale;
- mantenuti condizionali i casi con vintage, release archive o methodology
  manifest non ancora provati.

## Esito

Fonti:

- `ready`: 1;
- `conditional`: 5;
- `blocked`: 4.

Famiglie:

- `ready`: 0;
- `conditional`: 3 (`bank-balance-sheet-flow`, `cross-dollar-shock`,
  `cross-bank-flow-contraction`);
- `blocked`: 5 (`bank-loss-absorption`, `broad-equity-drawdown`,
  `broad-credit-quality-dispersion`, `funding-unsecured-tiering`,
  `funding-secured-repo-dislocation`).

## Cause principali

- FDIC aggregate parte nel 1984: solo 4 mesi prima di Continental Illinois,
  contro 60 richiesti;
- commercial paper parte nel 1997: 19 mesi prima di Russia/LTCM, contro 60,
  e il volume storico completo non e' provato;
- SOFR/TGCR/BGCR parte il 3 aprile 2018: 17 mesi prima di repo-stress 2019,
  contro 36;
- NASDAQCOM richiede pre-approvazione del titolare;
- AAA10Y e BAA10Y hanno vincoli proprietari Moody's;
- H.8 non prova vintages machine-readable completi per il 1984;
- BIS EER/LBS consente uso con attribuzione, ma i current histories e i break
  richiedono ancora vintage/release e methodology manifest.

## Evidenza

- network policy: `metadata-only-no-series-download`;
- osservazioni scaricate: 0;
- righe dataset/outer lette: 0;
- audit reale SHA-256:
  `5851dac52554a0885e93cadcac33de68f92b418911f12ad36f61c68b392329b1`.

## Decisione

Il gate non e' superato e l'acquisizione resta chiusa. Le cinque famiglie
bloccate sono ritirate senza fallback; le tre condizionali restano congelate ma
non acquisibili. E' autorizzata soltanto E14.7b: preregistrare task documentali
per le condizionali e sostituzioni indipendentemente motivate per le famiglie
ritirate, prima di qualunque download.

## Verifiche

- test mirati E14.7a: 4/4;
- regressione Python: 146/146;
- `compileall`: superato;
- test .NET: superati;
- `git diff --check`: superato;
- source hash e input hash: superati.
