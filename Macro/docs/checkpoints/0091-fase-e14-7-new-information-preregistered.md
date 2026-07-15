# Checkpoint 0091 - E14.7 new information preregistered

Data: 2026-07-15

## Obiettivo

Preregistrare una nuova ipotesi informativa meccanismo-specifica dopo il no-go
E14.6h, congelando fonti, direzioni, trasformazioni, firme per episodio e
ablation prima di qualsiasi acquisizione o nuova valutazione.

## Realizzato

- aggiunti schema, piano e contratto hash-bound E14.7;
- aggiunto il comando `e14-preregister-new-information`;
- congelate 8 famiglie informative, due per ciascuno dei quattro meccanismi;
- catalogate 10 fonti provider-primary con copertura, frequenza, classe di
  disponibilita' e limitazioni note;
- congelate 17 firme, esattamente una per episodio LOEO positivo, con onset,
  intensita', recovery e falsification condition separati;
- preregistrati missingness esplicita, regimi metodologici senza silent splice
  e ablation prima della popolazione.

## Famiglie

- banking-credit: `bank-loss-absorption`, `bank-balance-sheet-flow`;
- broad-market-repricing: `broad-equity-drawdown`,
  `broad-credit-quality-dispersion`;
- cross-border-growth: `cross-dollar-shock`,
  `cross-bank-flow-contraction`;
- funding-liquidity: `funding-unsecured-tiering`,
  `funding-secured-repo-dislocation`.

Le fonti verificate a livello di design comprendono FDIC, Federal Reserve H.8
e commercial paper, FRED/Nasdaq e Moody's, BIS EER/LBS e New York Fed reference
rates. La verifica web non equivale a eleggibilita': licenza, snapshot,
publication-date join e copertura devono ancora superare E14.7a.

## Evidenza

- meccanismi: 4;
- famiglie: 8;
- fonti: 10;
- firme episodio-specifiche: 17 (3 banking, 6 broad, 5 cross-border,
  3 funding);
- almeno una fonte nuova rispetto al catalogo v1 per ogni meccanismo;
- audit reale SHA-256:
  `4da83787c02b1f8af5f751234fa6805fe75d6e1ff2ce8092056118ac45ad6cae`.

## Decisione

La nuova ipotesi e' preregistrata, non validata. E' autorizzato soltanto E14.7a,
un audit read-only di accessibilita', licenza, copertura storica, vintage,
release semantics e break metodologici. Source acquisition, foundation,
taxonomy mutation, candidate generation, fitting, evaluation, ranking,
composizione, outer OOS e promozione restano chiusi.

## Verifiche

- test mirati E14.7: 3/3;
- regressione Python: 142/142;
- `compileall`: superato;
- test .NET: superati;
- `git diff --check`: superato;
- righe dataset/outer lette: 0.
