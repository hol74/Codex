# Checkpoint 0094 - E14.7c replacement source feasibility blocked

Data: 2026-07-15

## Obiettivo

Riesaminare le 3 famiglie condizionali preservate e le 5 sostituzioni E14.7b
con evidenza provider-primary su accesso, licenza, componenti, release,
vintages e metodologia, senza scaricare osservazioni.

## Realizzato

- aggiunti evidence schema, evidence pack e contratto hash-bound E14.7c;
- aggiunto il comando `e14-reaudit-replacement-source-feasibility`;
- verificato un roster esatto di 10 fonti e 8 famiglie;
- separata la copertura nominale dalla reale disponibilita' event-time;
- bloccata ogni fonte priva anche di una sola dimensione obbligatoria;
- mantenute chiuse acquisizione, foundation, taxonomy, candidati, fitting,
  evaluation, ranking, composizione, outer OOS e promozione.

## Esito

Fonti:

- `ready`: 1 (`fred-dtb3`);
- `blocked`: 9.

Famiglie:

- `ready`: 0;
- `blocked`: 8.

## Cause principali

- H.8: archivio datato online non prova il periodo causale pre-1984 e la
  current history incorpora revisioni e benchmark;
- BIS EER/LBS: metodologia e break sono documentati, ma non i vintages e le
  publication-date join provider-primary di tutti gli episodi;
- FDIC annual historical: copertura dal 1934, ma componenti, vintage,
  metodologia e termini di snapshot non sono tutti chiusi;
- Z.1: amounts outstanding dal 1945, ma archivio release online dal 1996,
  troppo tardi per Mexico 1994;
- DGS2/DGS10: copertura lunga, ma ALFRED documenta la serie dal 28 giugno 2005;
- DCD90: nessuno snapshot event-time provato per Russia/LTCM 1998;
- primary dealer NY Fed: dati dal 1998 e sei regimi documentati, ma revisioni,
  release immutabili e termini di snapshot non sono chiusi.

## Evidenza

- network policy: `provider-metadata-only-no-series-observation-download`;
- osservazioni scaricate: 0;
- righe dataset/outer lette: 0;
- audit reale SHA-256:
  `7dcfaa24e9df9c46f0e0ddfd499acf4eeab8f5343c85b970ddf268a7e0c36413`.

## Decisione

Il gate non e' superato. E' autorizzata soltanto E14.7d: preregistrare la
decisione fra chiusura E14, ricostruzione archivistica mantenendo lo standard
oppure scope post-2005 separatamente versionato. La observation date non puo'
sostituire implicitamente la publication availability.

## Verifiche

- test mirati E14.7c: 4/4;
- regressione Python: 154/154;
- `compileall`: superato;
- test .NET `--no-restore`: superati;
- audit deterministico e write-once: superati;
- source hash e input hash: superati.
