# Checkpoint 0126 - E14.7ai FDIC archive evidence remediated

Data: 2026-07-17

## Esito

E14.7ai ha corretto i quattro finding E14.7ah senza effettuare rete.

Il nuovo evidence manifest richiede per ogni quarter:

- evidence ID e request ID univoci;
- requested URL, final URL e redirect chain provider-primary;
- timestamp, status code e content type della risposta;
- file name, size e SHA-256 dei bytes raw;
- outcome e marker probatorio coerenti.

Map schema v3 usa un singolo array di 79 entry. Il validator semantico
fail-closed impone roster ordinato esatto 2006Q1-2025Q3, unicita' di quarter ed
evidence, corrispondenza outcome/hash, URL archivio esatto per record risolti e
prova `provider-no-record` per assenze confermate.

Audit schema v3 richiede il validator report. Un controllo separato lega i
conteggi resolved/confirmed-absent al contenuto validato di mappa e manifest.
Qualsiasi incoerenza blocca la pubblicazione.

Il contratto ha SHA-256
`ab5bff69326922731e8c0659b21e6dd0e53f2909740eeda7b8a001903cc48a03`.
L'audit ha SHA-256
`7c83b94019008a369715d81a979b7eb1e7b9201cec7be13527767dcf6a457ffb`.

Gli 8 test mirati coprono fixture valida e rifiuto di roster parziale,
duplicati, provenance off-provider, evidence riutilizzata, mismatch di outcome
o hash e conteggi audit incoerenti. L'intera suite di 310 test Python e' verde.

## Decisione

Evidence model, map/audit schema v3 e validator semantico sono pronti per
review, ma non autorizzano discovery o execution.

Il prossimo passo consentito e' E14.7aj: review indipendente hash-bound di
contratto, piano, schemi, validator, test e audit. Soltanto un esito positivo
potra' aprire la progettazione separata del discovery request catalog.

Rete, discovery catalog, execution gate, catalogo v3, source acquisition,
snapshot v2, trasformazioni, candidati, evaluation e outer OOS restano chiusi.
