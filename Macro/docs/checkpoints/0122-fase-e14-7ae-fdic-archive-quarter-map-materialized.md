# Checkpoint 0122 - E14.7ae FDIC archive quarter map materialized

Data: 2026-07-17

## Esito

E14.7ae ha materializzato offline una mappa immutabile e hash-bound per tutti
i 79 quarter FDIC QBP da 2006Q1 a 2025Q3. Il roster e gli URL
`www.fdic.gov` sono preservati byte-for-byte dal catalogo E14.7ac.

Il corpus locale congelato non contiene evidenza provider-primary hash-bound
che associ un `archive.fdic.gov` record ID a uno specifico quarter. Per evitare
associazioni inventate, tutte le 79 entry sono quindi marcate
`unresolved-no-hash-bound-local-evidence`, con discovery a runtime vietata.

La mappa ha SHA-256
`d63eee9ab7436f3ca161ca1b67a42235407cbf73d292d8ba9f126df97da30b2f`.
L'audit ha SHA-256
`2b24ed6fe52667a37ecf6cc4855c664b8e47b5543f4480a3fe606700ceafe5e9`.
Il contratto ha SHA-256
`6cf81ec601998bc906d55f2037672b44280538158796505b504ba57aacb0799b`.

Il comando registra zero richieste di rete, zero traversal archivio, zero
record ID inventati e zero righe metadata. I 5 test mirati e l'intera suite di
291 test Python sono verdi.

## Decisione

La remediation strutturale E14.7ae e' completa, ma non autorizza il gate
sostitutivo: la mappa contiene 79 disposizioni esplicite ma zero associazioni
archivio risolte.

Il prossimo passo consentito e' E14.7af, una review indipendente hash-bound che
decida se le disposizioni irrisolte eliminano correttamente la discrezionalita'
oppure se occorre preregistrare una raccolta provider-primary separata per
risolvere gli archive record ID. Rete, catalogo v3, snapshot v2, trasformazioni,
candidati, evaluation e outer OOS restano chiusi.
