# Checkpoint 0124 - E14.7ag FDIC archive evidence preregistered

Data: 2026-07-17

## Esito

E14.7ag ha preregistrato offline il protocollo provider-primary necessario a
superare i finding E14.7af. Per ciascuno dei 79 quarter sono ammessi soltanto
due esiti:

- `resolved-provider-archive-record`, con record ID, URL
  `archive.fdic.gov` esatto ed evidenza raw legata per hash;
- `confirmed-absent-provider-primary`, con prova provider-primary legata per
  hash che dimostri l'assenza del record.

Sono vietati placeholder irrisolti, inferenze da quarter-end o Last-Modified,
record ID stimati e fonti secondarie isolate. La pubblicazione parziale e'
vietata: i 79 quarter devono formare una partizione completa e univoca dei due
esiti.

Sono stati versionati:

- map schema v2, capace di rappresentare entrambi gli esiti;
- map audit schema v2, chiuso sulle sezioni checks, inventory, protocol e
  decision;
- piano di raccolta e contratto hash-bound;
- comando CLI e audit di preregistrazione fail-closed.

Il contratto ha SHA-256
`9cc8d9bcf8c9d61de68957a3bf5bee74eef5b2f8531d1a7c5a97d554aeab79f0`.
L'audit ha SHA-256
`ce3b5f460988adb55f3379dbd43c0c1aa31e8414574547e88dfb31ad6da70b87`.

Il comando registra 79 quarter ancora in attesa di evidenza, zero rete, zero
raw artifact, zero request catalog e nessuna mappa v2. I 5 test mirati e
l'intera suite di 299 test Python sono verdi.

## Decisione

Il disegno provider-primary e gli schemi v2 sono preregistrati, ma non
autorizzano richieste o discovery. Il prossimo passo consentito e' E14.7ah:
review indipendente hash-bound di piano, contratto, schemi v2, implementazione
e audit.

Soltanto un esito positivo potra' autorizzare la progettazione separata del
request catalog di discovery e del successivo execution gate. Rete, catalogo
v3, source acquisition, snapshot v2, trasformazioni, candidati, evaluation e
outer OOS restano chiusi.
