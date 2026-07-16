# Checkpoint 0121 - E14.7ad FDIC metadata request catalog review blocked

Data: 2026-07-16

## Esito

La review indipendente hash-bound di E14.7ac ha restituito `needs_changes`.
Sono stati confermati:

- hash di contratto, piano, catalogo, audit, schema e implementazione;
- roster ordinato e univoco di 79 quarter da 2006Q1 a 2025Q3;
- corrispondenza dei 79 URL con l'indice QBP congelato;
- tre definizioni di template legate per hash;
- zero richieste e guard fail-closed della preregistrazione;
- pertinenza provider-primary di `archive.fdic.gov` per le date storiche.

La review ha pero' rilevato due finding bloccanti:

- `ARCHIVE_RECORD_ID_EXPANSIONS_NOT_FROZEN`: manca una mappa completa da
  `quarterId` a record ID o URL archivio esatto;
- `ARCHIVE_DISCOVERY_RETAINS_RUNTIME_DISCRETION`: i seed non definiscono una
  traversal deterministica e limitata capace di produrre le 79 espansioni.

Il template `https://archive.fdic.gov/view/fdic/{ARCHIVE_RECORD_ID}` e' legato
per hash soltanto nella forma; nessun `ARCHIVE_RECORD_ID` e' congelato nel
catalogo. Il nuovo gate operativo non e' quindi autorizzabile.

Il receipt della review ha SHA-256
`a9b3564c3bdafec43e02dd2154e3ca532a4173aad7b8e7f0c18fdeb878819b6e`.
I 3 test mirati e l'intera suite di 286 test Python sono verdi. Il receipt e'
conforme allo schema chiuso della review.

## Decisione

E14.7ad mantiene chiusa la raccolta metadata. Il solo passo ammesso e' una
remediation separata che materializzi una mappa immutabile e hash-bound per
tutti i 79 quarter verso URL o record ID `archive.fdic.gov`, usando entry
esplicitamente irrisolte quando nessun record esiste.

La mappa dovra' essere sottoposta a nuova review indipendente prima di
versionare un gate sostitutivo. Catalogo source-acquisition v3, snapshot v2,
rete, payload event-time e downstream restano vietati.
