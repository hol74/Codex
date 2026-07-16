# Checkpoint 0119 - E14.7ab FDIC metadata collection preflight blocked

Data: 2026-07-16

## Esito

E14.7ab ha fermato il collector prima della rete. Il gate E14.7aa congela
host e limiti operativi, ma il relativo piano non contiene gli URL seed esatti
ne' template di richiesta legati per hash. Costruire tali richieste durante
l'esecuzione introdurrebbe discrezionalita' non preregistrata.

Il preflight fail-closed registra quindi:

- `EXACT_SEED_URLS_NOT_FROZEN`;
- `REQUEST_TEMPLATES_NOT_HASH_BOUND`;
- zero richieste di rete, zero righe metadata e zero raw artifact;
- nessun ledger e nessun request catalog pubblicato;
- catalogo v3 e snapshot v2 ancora assenti.

Il contratto del preflight ha SHA-256
`066ade723630a5e831256be99d851242b6818b6b196500b78e7de80eca04df78`.
L'audit ha SHA-256
`07cffc539c4e3bd02f1994beb26dc15230ec52160a93376e20b0ff4007b107c9`.

La ricognizione provider-primary ha inoltre individuato che le pagine storiche
con data di rilascio esplicita possono risiedere su `archive.fdic.gov`, mentre
E14.7aa consente soltanto `www.fdic.gov`. Questa evidenza non modifica il gate
esistente e dovra' essere trattata nella remediation versionata.

I 5 test mirati e l'intera suite di 278 test Python sono verdi. L'audit e'
conforme allo schema preregistrato.

## Decisione

La raccolta metadata FDIC non e' autorizzata. E' autorizzata soltanto la
preregistrazione di un request catalog metadata-only che congeli URL
provider-primary esatti e template hash-bound. La remediation deve decidere in
modo esplicito l'eventuale aggiunta di `archive.fdic.gov`; un gate operativo
nuovamente versionato e sottoposto a review indipendente e' obbligatorio prima
di qualsiasi richiesta.

Catalogo v3, snapshot v2, acquisizione completa, trasformazioni, candidati,
evaluation e outer OOS restano chiusi.
