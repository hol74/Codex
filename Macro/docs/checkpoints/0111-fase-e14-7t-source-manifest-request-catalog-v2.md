# Checkpoint 0111 - E14.7t manifest e request catalog v2

Data: 2026-07-16

## Esito

La preregistrazione E14.7t ha pubblicato tre artefatti immutabili:

- manifest v2 SHA-256 `cbe3e50768381c6772a8a5b70efa04fe62fb27d4f33b5623f5f7fc8caeb128dc`;
- request catalog v2 SHA-256 `cf4d1c8643d4123ff7ac3ef3bd780766cd46f4b3fbddeda858b4682ffcc36935`;
- preregistration audit v2 SHA-256 `f2a2e8cfe02b89c2f10df4377623c4450466186e43ebee6ec0888da91d432827`.

Il roster contiene H.8, FDIC QBP, DGS2, DGS10, G.5, DCPF3M e DTB3. H.10 e i
suoi raw path sono assenti. Le due famiglie ridisegnate sono
`bank-release-archived-balance-sheet-post2005-v2` e
`cross-g5-dollar-shock-post2005-v2`; le famiglie Treasury e funding restano
semanticamente invariate.

Gli 11 template congelano discovery ed espansione provider-primary. G.5
richiede 240 mesi unici 2006-01..2025-12 e adjudication per duplicati o
correzioni. FDIC richiede 79 trimestri 2006Q1..2025Q3, esclude 2025Q4 e vieta
di usare quarter-end come prova di pubblicazione.

Il reviewer indipendente ha bloccato una prima versione per incoerenza fra gli
11 input dell'audit e lo schema e per strutture nested troppo permissive. Gli
schema sono stati chiusi, gli hash risincronizzati e la validazione
deterministica estesa. Dopo le correzioni il reviewer ha approvato senza
blocker; gli otto test mirati e l'intera suite di 237 test sono verdi.

## Decisione

Manifest e catalogo sono pronti, ma non eseguibili direttamente dal vecchio
executor v1. E' autorizzato soltanto un nuovo gate metadata fail-closed legato
ai loro hash esatti. Network request, acquisizione, raw artifact,
trasformazione, candidati, evaluation e outer OOS restano chiusi.
