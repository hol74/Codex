# Checkpoint 0125 - E14.7ah FDIC archive evidence review blocked

Data: 2026-07-17

## Esito

La review indipendente hash-bound del protocollo E14.7ag ha restituito
`needs_changes`. Sono stati confermati:

- hash esatti di contratto, review precedente, piano, schemi, audit e
  implementazione;
- rappresentazione distinta dei due esiti ammessi;
- evidenza raw legata per hash per record risolti e assenze confermate;
- audit schema chiuso e zero rete;
- mantenimento dei blocchi su discovery, execution e downstream.

La review ha pero' rilevato quattro finding bloccanti:

- l'artefatto evidence non lega hash e bytes all'URL esatto, request ID e
  metadata di retrieval provider-primary;
- map schema v2 non impone roster 79/79, unicita' interna o esclusione dei
  duplicati tra resolved e confirmed-absent;
- audit schema v2 non impone che i due conteggi sommino a 79 ne' li lega al
  contenuto della mappa e del manifest evidence;
- il divieto di pubblicazione parziale e' soltanto dichiarativo: manca un
  producer fail-closed revisionato che applichi gli invarianti.

Il receipt della review ha SHA-256
`6a346c6db8069224038f6cd3f9024300116e6f89f9ee783450704a8a37d99eec`.
I 3 test mirati verificano schema chiuso, hash e decisione; l'intera suite di
302 test Python e' verde.

## Decisione

E14.7ag migliora il modello, ma non risolve ancora i finding E14.7af. La
progettazione del discovery request catalog non e' autorizzata.

Il prossimo passo deve versionare un evidence model che leghi ogni artefatto a
URL, request identity e metadata di retrieval esatti; aggiungere un validator
fail-closed per roster 79/79, unicita' e disgiunzione dei due esiti; rafforzare
la coerenza fra audit, mappa e manifest evidence; quindi ripetere la review
indipendente.

Rete, discovery catalog, execution gate, catalogo v3, source acquisition,
snapshot v2, trasformazioni, candidati, evaluation e outer OOS restano chiusi.
