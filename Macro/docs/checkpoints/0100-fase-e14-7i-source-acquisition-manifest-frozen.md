# Checkpoint 0100 - E14.7i manifest acquisizione fonti

Data: 2026-07-16

## Esito

Il manifest di acquisizione post-2005 e' stato congelato senza richieste di
rete o osservazioni. Contiene sette fonti metadata-ready e una famiglia per
ciascun meccanismo:

- banking-credit: H.8 e FDIC QBP;
- broad-market-repricing: DGS2 e DGS10;
- cross-border-growth: H.10;
- funding-liquidity: DCPF3M e DTB3.

La finestra e' `2006-01-01` - `2025-12-31`. Per ogni fonte sono congelati
provider, locator, frequenza, serie o tabelle, semantica as-of, regimi
metodologici e percorso raw. La policy richiede bytes originali, SHA-256,
timestamp di retrieval e metadati release/vintage; acquisizioni parziali o
break inattesi falliscono chiusi.

Il manifest ha SHA-256
`2203aba40264054476a28b6c162e5eecc7346563bfb8a26f1339e65033881b90`;
l'audit ha SHA-256
`2a9f7d4f0cd9e833c96054dca263f646082a6ab0ddf28959e91001f89f7bb991`.

## Limiti e prossimo passo

Il gate ha effettuato zero richieste di rete, acquisito zero osservazioni e
scritto zero raw artifact. Esecuzione dell'acquisizione, trasformazione feature,
candidati, evaluation e outer OOS restano chiusi. Il prossimo passo ammesso e'
un gate di esecuzione fail-closed contro l'hash esatto del manifest.
