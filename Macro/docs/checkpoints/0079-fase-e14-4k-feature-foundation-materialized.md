# Checkpoint 0079 - E14.4k feature foundation materialized

Data: 2026-07-15

## Obiettivo

Popolare e manifestare la foundation delle feature dei quattro detector E14,
preservando cutoff, provenienza, discontinuita' metodologiche e missingness,
senza generare candidati.

## Snapshot congelati

Sono stati acquisiti da fonti ufficiali e legati tramite SHA-256:

| Snapshot | SHA-256 |
| --- | --- |
| Cboe VIX history | `0b2ed656686791c38d4230a2cedeb169a4b56014323079c740722ab5b3bebda9` |
| FRED BAA10Y | `265ed909e3bd010f1b3b8b9799af375fe526c294d34ccbf302b511701cdda90b` |
| FRED TEDRATE | `291d6007c287e3a1a56fff7879dcfa5aaa44620bc0a68cb2ab8ccf032795c99d` |
| FRED DTWEXB | `c7b0270b4bc75cfae32127a5d07f77093c0e9241052f39a62d1a4d0c277db699` |
| FDIC QBP time series Q4 2025 | `97eaf69c51e1e8b373dc0837219ba5f5e8c1ffee101b8c1cadc07d0cdcd42253` |

## Materializzazione

| Serie | Osservazioni | Copertura |
| --- | ---: | --- |
| VIX massimo mensile | 432 | 1990-01 / 2025-12 |
| BAA10Y massimo mensile | 480 | 1986-01 / 2025-12 |
| TEDRATE massimo mensile | 433 | 1986-01 / 2022-01 |
| DTWEXB massimo cambio assoluto giornaliero | 300 | 1995-01 / 2019-12 |
| FDIC quota prestiti noncurrent | 167 | 1984Q1 / 2025Q3 |

Le cinque serie alimentano sei binding: BAA10Y e' usato sia dal detector
broad-market sia dal detector banking-credit. Tutti i transform restano
`inner-only` e nessuna soglia viene stimata in questo step.

## As-of e discontinuita'

- nessuna osservazione supera il cutoff 2025-12-31;
- TEDRATE termina nel regime LIBOR e non viene riempito con SOFR;
- DTWEXB termina nel regime goods-only e non viene unito al successore;
- periodi precedenti la copertura e valori assenti restano missing, mai zero;
- FDIC usa un lag conservativo di 60 giorni dal quarter-end: Q4 2025 resta
  escluso perche' non ancora disponibile al cutoff.

Gli snapshot daily FRED e il workbook FDIC rappresentano storia corrente
congelata, non una ricostruzione vintage perfetta. Il limite e' registrato sia
nella foundation sia nel lock e impedisce di dichiarare `strictVintageReady`.

## Esito e autorizzazioni

Stato: `FEATURE_FOUNDATION_MATERIALIZED_WITH_VINTAGE_LIMITATIONS`.

- foundation materializzata: si;
- sei binding popolati e manifestati: si;
- strict vintage ready: no;
- progettazione protocollo E14.4l: autorizzata;
- candidate generation, outer OOS e promozione: non autorizzati.

Hash principali:

- foundation: `bca70e5f5ca224fe23e4b29970dc651a2b708c047e3364a3575a235ae80a64b9`;
- lock: `34448522085f5949e341cc62cda3b8088a47eac9a7f01ea9c5f0a7220d9a61dc`;
- audit: `0e989608ca76975a41e433d7e5d8d3b9ec8d0a00fc0b7649be4ad060b44db940`.

## Implementazione e verifiche

- schema: `models/e14-mechanism-feature-foundation-schema-v1.json`;
- contratto: `models/e14-mechanism-feature-foundation-contract-v1.json`;
- lock: `models/e14-mechanism-feature-foundation-lock-v1.json`;
- modulo: `regime_eval/e14_feature_foundation.py`;
- comando: `e14-materialize-feature-foundation`;
- test mirati: 3/3;
- suite Python completa: 105/105;
- compilazione bytecode: superata;
- test .NET: superati;
- `git diff --check`: superato.

## Prossimo passo

E14.4l deve congelare una grammatica research a quattro detector legata agli
hash della tassonomia v5 e del lock E14.4k. Potra' riusare i controlli causali,
train-only, inner-only e missingness-explicit di E13, ma non la sua fondazione
E12 ne' la grammatica a due task. Prima di generare candidati sara' necessario
rieseguire un gate di readiness che consideri esplicitamente i limiti vintage.
