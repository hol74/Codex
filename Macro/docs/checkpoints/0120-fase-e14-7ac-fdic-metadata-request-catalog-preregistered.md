# Checkpoint 0120 - E14.7ac FDIC metadata request catalog preregistered

Data: 2026-07-16

## Esito

E14.7ac ha preregistrato senza rete il request catalog metadata-only richiesto
dal preflight E14.7ab. Dal `past-qbp-index.html` gia' congelato e legato per
hash sono stati estratti esattamente 79 URL provider-primary, da 2006Q1 a
2025Q3, escludendo 2025Q4.

Il catalogo congela:

- due seed URL esatti: l'indice QBP corrente e il record archivio FDIC 9120;
- tre template, ciascuno dotato del proprio SHA-256 canonico;
- 79 request ID e URL trimestrali esatti su `www.fdic.gov`;
- `archive.fdic.gov` come estensione host soltanto proposta;
- uso limitato alla discovery della prova della data di pubblicazione.

Tutte le 79 date restano irrisolte. Quarter-end, Last-Modified, stime di lag e
fonti secondarie restano sostituti vietati.

Il contratto ha SHA-256
`ca5e888cb65e7bbf93b257b2e758fd8a1b2b831ac98182cbb490ec923e19c5d6`.
Il catalogo ha SHA-256
`9498ed5bc1fa399aeb54aa1409aad5384416d1b1dd71bbaa8e608407def280f1`.
L'audit ha SHA-256
`6c8f45e4e5f11c72b749a059b497e14de62deb480e4ad3f2c0a491b07a88abc4`.

I 5 test mirati e l'intera suite di 283 test Python sono verdi. Catalogo e
audit sono conformi agli schemi preregistrati.

## Decisione

Il request catalog metadata-only e' preregistrato, ma rete ed estensione host
non sono autorizzate. Il prossimo passo deve essere una review indipendente
hash-bound dei due seed, delle 79 richieste, dei tre template e della proposta
`archive.fdic.gov`. Soltanto dopo un esito positivo potra' essere versionato un
nuovo gate operativo.

Catalogo source-acquisition v3, snapshot v2, payload event-time, trasformazioni,
candidati, evaluation e outer OOS restano chiusi.
