# Checkpoint 0116 - E14.7y FDIC metadata collection preregistered

Data: 2026-07-16

## Esito

E14.7y ha preregistrato, senza rete, la raccolta metadata-only delle 79 prove
provider-primary richieste per le date effettive di pubblicazione FDIC QBP.

Il roster deterministico copre esattamente `2006Q1`-`2025Q3` e mantiene tutte
le 79 righe nello stato non risolto. Per ogni riga futura sono obbligatori
quarter, data effettiva, URL FDIC, tipo di evidenza, SHA-256 della risposta e
timestamp di cattura. Sono vietati come sostituti:

- quarter-end;
- header HTTP `Last-Modified`;
- lag stimati;
- fonti secondarie non FDIC.

Il contratto ha SHA-256
`42b4c7b3b8761f956aee7eec27d1a2db230d99c8229440a1c3c0f012caba4ffc`.
L'audit preregistrato ha SHA-256
`22c537fe81603169035b37bbc9635e8d390191a476fa0de51bd3ad3121a739f4`.

Il protocollo registra zero richieste di rete, zero righe metadata raccolte,
zero raw artifact e zero cataloghi materializzati. Catalogo v3 e snapshot v2
restano assenti. I 6 test mirati e l'intera suite di 266 test Python sono
verdi.

## Decisione

Il disegno della raccolta metadata-only e' preregistrato, ma l'esecuzione di
rete non e' autorizzata. Il prossimo passo consentito e' una review indipendente
del contratto, del roster, dei campi obbligatori e dei guard di esecuzione. Solo
un gate successivo e separato potra' autorizzare richieste metadata-only verso
`www.fdic.gov`; catalogo v3, payload event-time, acquisizione completa, feature,
candidati, evaluation e outer OOS restano vietati.
