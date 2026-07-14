# Checkpoint 0060 - E14.1 information audit

Data: 2026-07-14

## Obiettivo

Stabilire se il fallimento E13 dipende principalmente da formule, feature,
label o copertura, senza generare o selezionare nuovi candidati.

## Realizzato

- congelato `e14-information-audit-contract-v1` sugli input E12-E13;
- analizzate esclusivamente le 84 date inner;
- confrontate distribuzioni e separabilita' marginale di cinque severita';
- costruite firme feature-specifiche dei tre episodi finanziari;
- misurata la sovrapposizione dei due aggregatori E13 sui 23 contrasti curati;
- mantenuti 54 mesi non etichettati fuori dalle metriche di classe;
- confermato un solo episodio recessivo osservabile.

## Esito

Le feature broad-market non separano stabilmente positivi e contrasti: AUC
direzionale da `0,292` a `0,752` e range overlap dal `53,5%` al `95,7%`.
SOFR-EFFR raggiunge AUC `1,0` e zero overlap, ma su un campione molto piccolo,
con copertura solo dal 2018 e firme profondamente diverse tra episodi.

I contrasti sono inflation/tightening, non veri negativi confermati. Il
trade-off E13 e' quindi insieme informativo e ontologico: una formula globale
non distingue meccanismi eterogenei, e la label corrente non stabilisce sempre
se una reazione durante il tightening sia corretta o falsa.

## Identita' degli artefatti

- audit contract SHA-256:
  `b499fb2ee246f2f3a971d35d3a5797db7ec5cdaffcd66c5c01bb8d9ded1943b9`;
- report SHA-256:
  `2630eccf3deea2945a1ac244b5cb5487a25e938a007905fa2539583c91df25b5`.

## Decisione

Non aprire E14 con nuovi modelli. Prima correggere tassonomia/hard negatives,
studiare estensione storica della foundation e definire detector per
meccanismo. Il dettaglio e' in `docs/e14-riesame-problema-informativo.md`.

## Verifica

- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 54/54 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- report deterministico, write-once e inner-only;
- zero candidati, ranking, gate o promozioni;
- zero righe outer-test;
- rifiuto di un contratto che autorizza uso diagnostico dell'outer.
