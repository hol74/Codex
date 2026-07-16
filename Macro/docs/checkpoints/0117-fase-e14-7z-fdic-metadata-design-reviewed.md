# Checkpoint 0117 - E14.7z FDIC metadata design reviewed

Data: 2026-07-16

## Esito

Un reviewer indipendente ha verificato integralmente contratto, piano, schema,
audit, implementazione e test della preregistrazione E14.7y. La decisione e'
`accept` con tutti i nove assessment positivi:

- hash binding esatti;
- roster ordinato di 79 quarter da `2006Q1` a `2025Q3`;
- campi probatori sufficienti;
- quarter-end, `Last-Modified`, lag stimati e fonti secondarie vietati;
- host `www.fdic.gov` congelato e redirect off-provider vietati;
- zero rete e zero righe raccolte dalla preregistrazione;
- esecuzione metadata, catalogo v3 e downstream ancora non autorizzati;
- guard fail-closed e output immutabile supportati dai test.

La receipt conforme allo schema ha SHA-256
`8fa7948109b0e519d847bb07750a07daa6d2a554a4bd8ed8121e51aee7591444`.
I 6 test mirati e l'intera suite di 266 test Python restano verdi.

## Decisione

Il disegno metadata-only e' accettato. La review non esegue e non autorizza
direttamente richieste di rete. Il prossimo passo consentito e' un gate
separato, hash-bound alla receipt, che congeli budget, redirect policy,
content-type, limiti byte, retry e pubblicazione atomica prima di autorizzare
la raccolta metadata-only. Catalogo v3, snapshot v2, payload event-time,
acquisizione completa, feature, candidati, evaluation e outer OOS restano
vietati.
